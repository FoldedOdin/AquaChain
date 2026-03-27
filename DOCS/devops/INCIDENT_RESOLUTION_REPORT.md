# AquaChain — DevOps Incident Resolution Report

**Date:** March 25–27, 2026
**Environment:** Production (dev stage) — AWS ap-south-1
**Role:** DevOps Engineer
**Status:** Resolved

---

## Overview

This report documents the investigation, root cause analysis, and resolution of three production incidents affecting the AquaChain IoT water quality monitoring platform. All issues were identified through live error traces, CloudWatch logs, and direct Lambda invocation testing — without any downtime to unaffected services.

---

## Incident 1 — Technician Assignment Returning HTTP 502

### Symptom
Admin dashboard was unable to assign technicians to orders. Every `PUT /api/orders/{orderId}/status` request returned HTTP 502 with "Internal server error" in the browser console.

### Investigation

1. Identified the API Gateway endpoint via `aws apigateway get-resources` — confirmed route `PUT /api/orders/{orderId}/status` was wired to Lambda `aquachain-update-order-status-dev`, not the enhanced order management Lambda.
2. Invoked the Lambda directly using `aws lambda invoke` with a test payload — received a Python `AttributeError` traceback instead of a valid response.
3. Root cause confirmed from CloudWatch logs:

```
AttributeError: <botocore.errorfactory.DynamoDBExceptions object> has no attribute ValidationException
```

The `except` clause in `update_order_status.py` referenced `dynamodb.meta.client.exceptions.ValidationException` — which does not exist on the DynamoDB boto3 client. Python evaluates `except` clauses at runtime, so this crashed the Lambda on every invocation before any response could be returned, causing API Gateway to emit a 502.

4. Secondary issue: `ORDERS_TABLE` environment variable was set to `aquachain-table-orders-dev` but orders were stored in `aquachain-orders`. Confirmed by scanning both tables.

### Resolution

- Removed the invalid `ValidationException` catch block from `lambda/orders/update_order_status.py`
- Corrected `ORDERS_TABLE` env var on `aquachain-update-order-status-dev` back to `aquachain-orders`
- Redeployed Lambda via `aws lambda update-function-code`
- Verified fix with direct Lambda invocation — returned HTTP 200

### Files Changed
- `lambda/orders/update_order_status.py`

---

## Incident 2 — COD and Online Orders Not Being Placed (Silent Failure)

### Symptom
Consumer ordering flow appeared to complete (no visible error) but orders were never confirmed. Both COD and Online payment paths were affected. No error banner was shown to the user.

### Investigation

**COD path:**
The `CODConfirmationTimer` component calls `onConfirm()` (which is `handleCODConfirm`) inside a `setTimeout` callback. `handleCODConfirm` is an `async` function but `onConfirm` is typed as `() => void`. When `createOrder` threw an error for any non-profile reason, the catch block re-threw it — but since it was inside a `setTimeout`, the rejection was unhandled and silently swallowed by the JavaScript runtime. React never saw it, no error state was set, and the flow just stopped.

**Online payment path:**
`RazorpayCheckout` component already verifies the payment with the backend before calling `onSuccess`. `OrderingFlow.handlePaymentSuccess` then called `paymentService.verifyPayment()` a second time. The second call failed because the payment record was already marked `COMPLETED` in DynamoDB, throwing "Payment verification failed" — which sent the user back to the payment method screen instead of the success screen.

**COD payment record race condition:**
After `await createOrder()` succeeded, the code checked `state.currentOrder?.id` to get the new order ID for the COD payment record. React state updates are asynchronous — `state.currentOrder` was still `null` at that point, so the COD payment record was never created.

### Resolution

**Frontend (`OrderingFlow.tsx`):**
- Removed duplicate `verifyPayment` call from `handlePaymentSuccess` — trusted that `RazorpayCheckout` already verified
- Changed both `handleCODConfirm` and `handlePaymentSuccess` catch blocks to handle all errors locally (no re-throw into void)
- On error, navigate back to `payment-method` step where `state.error` is displayed

**Frontend (`OrderingContext.tsx`):**
- Changed `createOrder` return type from `Promise<void>` to `Promise<string>` — returns the created order ID directly
- COD handler now uses the returned ID for the payment record instead of reading stale React state

### Files Changed
- `frontend/src/components/Dashboard/OrderingFlow.tsx`
- `frontend/src/contexts/OrderingContext.tsx`

### Deployment
- Built frontend: `npm run build`
- Deployed to S3: `aws s3 sync build/ s3://aquachain-frontend-dev-758346259059 --delete`
- Invalidated CloudFront cache: `aws cloudfront create-invalidation --paths "/*"`

---

## Incident 3 — Technician Assignment Failing on New Orders (HTTP 500)

### Symptom
After the ordering flow was fixed and new orders were being created, technician assignment started returning HTTP 500 on those new orders. Previously created orders were unaffected.

### Investigation

Pulled CloudWatch logs for `aquachain-update-order-status-dev` immediately after a failed request:

```
TypeError: Float types are not supported. Use Decimal types instead.
  File "update_order_status.py", line N, in handler
    update_response = orders_table.update_item(...)
  File ".../boto3/dynamodb/types.py", in _serialize_m
```

The `AssignTechnicianModal` sends `technicianRating` in the metadata payload (e.g. `4.5`). Python's `json.loads()` parses JSON numbers with decimals as native `float`. boto3's DynamoDB resource client rejects `float` values — only `Decimal` is accepted for numeric types.

The `metadata` dict was being written directly into both the `statusHistory` list entry and the `technician` object without any type conversion.

### Resolution

Added `sanitize_for_dynamodb()` helper to `update_order_status.py`:

```python
def sanitize_for_dynamodb(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: sanitize_for_dynamodb(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [sanitize_for_dynamodb(i) for i in obj]
    return obj
```

Applied to the entire `metadata` dict at parse time — covers all nested fields including `technicianRating`, any future float fields, and strips `None` values (also rejected by DynamoDB).

Redeployed Lambda and verified with a float rating payload — returned HTTP 200.

### Files Changed
- `lambda/orders/update_order_status.py`

---

## Additional Work — Enhanced Order Management Lambda Deployment Fix

### Problem
`enhanced_order_management.py` imports shared utilities (`structured_logger`, `input_validator`, `error_handler`) from a `shared/` directory. The manual deploy script (`deploy_enhanced_order_management.bat`) only zipped the handler file without `shared/`, causing `ModuleNotFoundError` at Lambda cold start → 502.

Additionally, the handler path in CDK is `orders/enhanced_order_management.lambda_handler`, meaning the file must be at `orders/enhanced_order_management.py` inside the zip — not at the root.

### Resolution

- Added fallback `sys.path` entries in `enhanced_order_management.py` to handle both CDK-bundled and manual deploy layouts
- Rewrote `deploy-with-shared.bat` to use a separate `create_zip.py` script (avoids Windows batch `^` continuation issues inside `python -c`)
- `create_zip.py` places the handler at `orders/enhanced_order_management.py` and shared modules at `shared/*.py` inside the zip

### Files Changed
- `lambda/orders/enhanced_order_management.py`
- `lambda/orders/deploy-with-shared.bat`
- `lambda/orders/create_zip.py` (new)

---

## Database Cleanup — Orphaned and Duplicate Records

### Problem
DynamoDB tables contained stale records from previous development/testing activity:

**AquaChain-Users table:**
- 7 ghost entries with IDs in format `user-17XXXXXXXXX`
- Only contained `lastLogin`, `updatedAt`, `userId` — no email, role, or profile data
- Created by failed or incomplete Cognito login flows

**aquachain-table-technicians-dev table:**
- 3 duplicate technician entries using old `PK`/`SK` schema (format: `TECHNICIAN#tech-001`)
- 1 completely blank entry with only `PK`, `SK`, `status` fields
- These were duplicates of real technicians already stored with proper `userId` keys

### Resolution

Wrote and executed a targeted cleanup script that:
- Deleted only `user-XXXXXXXXX` prefixed entries from `AquaChain-Users`
- Deleted only entries with `PK`/`SK` keys and no `userId` from the technicians table
- Left all real users and technicians (Cognito UUID keys) untouched

**Before cleanup:**
- `AquaChain-Users`: 12 items (5 real + 7 orphaned)
- `aquachain-table-technicians-dev`: 8 items (4 real + 4 junk)

**After cleanup:**
- `AquaChain-Users`: 5 items (1 admin, 2 consumers, 2 technicians)
- `aquachain-table-technicians-dev`: 4 items (all real)

---

## Summary of All Changes

| Area | Change | Type |
|------|--------|------|
| `update_order_status.py` | Remove invalid `ValidationException` catch | Bug fix |
| `update_order_status.py` | Add `sanitize_for_dynamodb()` for float→Decimal conversion | Bug fix |
| `enhanced_order_management.py` | Fix `sys.path` for shared module resolution | Bug fix |
| `deploy-with-shared.bat` | Rewrite to correctly bundle shared/ and use orders/ prefix | Fix |
| `create_zip.py` | New helper script for Lambda packaging | New file |
| `OrderingFlow.tsx` | Remove duplicate payment verification | Bug fix |
| `OrderingFlow.tsx` | Fix silent error swallowing in setTimeout callbacks | Bug fix |
| `OrderingContext.tsx` | Return order ID from `createOrder` | Bug fix |
| Lambda env var | `ORDERS_TABLE` corrected to `aquachain-orders` | Config fix |
| DynamoDB | Remove 7 orphaned users + 4 junk technician records | Cleanup |
| CloudFront | Cache invalidation after frontend deploy | Deployment |

---

## Deployment Commands Reference

```bash
# Deploy update_order_status Lambda
Compress-Archive -Path update_order_status.py -DestinationPath fix.zip -Force
aws lambda update-function-code --function-name aquachain-update-order-status-dev \
  --zip-file fileb://fix.zip --region ap-south-1
aws lambda wait function-updated --function-name aquachain-update-order-status-dev

# Deploy enhanced_order_management Lambda (with shared deps)
cd lambda/orders
.\deploy-with-shared.bat

# Deploy frontend
cd frontend
npm run build
aws s3 sync build/ s3://aquachain-frontend-dev-758346259059 --delete --region ap-south-1
aws cloudfront create-invalidation --distribution-id E30XQUUQNWL1O4 --paths "/*"

# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name aquachain-update-order-status-dev \
  --environment "Variables={ORDERS_TABLE=aquachain-orders,...}" \
  --region ap-south-1
```

---

## Lessons Learned

1. **Python `except` clauses are evaluated at runtime** — referencing a non-existent exception attribute crashes the Lambda before any handler logic runs, producing a 502 with no useful error in the response body. Always validate exception class names against the boto3 client's actual exception factory.

2. **React state is asynchronous** — never read `state.X` immediately after dispatching an action that sets it. Return values from async functions instead.

3. **`async` functions called from `setTimeout` callbacks need their own error handling** — unhandled rejections in timer callbacks are silently swallowed in React apps.

4. **boto3 DynamoDB resource client rejects Python `float`** — always convert to `Decimal` before writing. A recursive sanitizer applied at the entry point is more reliable than converting field by field.

5. **Manual deploy scripts must mirror CDK bundling structure** — the handler path in CDK (`orders/enhanced_order_management.lambda_handler`) dictates the zip layout. Mismatches cause silent 502s that look identical to import errors.

6. **Always verify which Lambda an API Gateway route actually invokes** — `aws apigateway get-integration` is the ground truth. CDK stacks and manual deploys can create multiple Lambdas for the same logical function.
