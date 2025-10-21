# Deployment Procedures for Design System Updates

## Overview

This document outlines comprehensive deployment procedures for design system updates, ensuring safe, reliable, and coordinated rollouts of design changes across the AquaChain application ecosystem. These procedures minimize risk, maintain system stability, and provide clear rollback strategies.

## Deployment Architecture

### Design System Components

```
Design System Package
├── Design Tokens (JSON/CSS)
├── Component Library
├── Documentation Site
├── Usage Guidelines
└── Migration Tools
```

### Deployment Environments

1. **Development**: Local development and feature branches
2. **Staging**: Integration testing and stakeholder review
3. **Production**: Live application serving users
4. **Documentation**: Public-facing design system documentation

## Pre-Deployment Procedures

### 1. Design System Validation

#### Token Validation

```bash
#!/bin/bash
# validate-design-tokens.sh

echo "🔍 Validating design tokens..."

# Check token structure
npm run validate:tokens:structure

# Validate accessibility compliance
npm run validate:tokens:accessibility

# Check for breaking changes
npm run validate:tokens:breaking-changes

# Validate token usage in components
npm run validate:tokens:usage

echo "✅ Design token validation complete"
```

#### Component Validation

```bash
#!/bin/bash
# validate-components.sh

echo "🔍 Validating component library..."

# Run component tests
npm run test:components

# Validate accessibility
npm run test:a11y:components

# Check visual regression
npm run test:visual:components

# Validate API consistency
npm run validate:component-apis

# Check documentation completeness
npm run validate:component-docs

echo "✅ Component validation complete"
```

### 2. Impact Assessment

#### Breaking Change Analysis

```javascript
// breaking-change-analyzer.js
const fs = require('fs');
const semver = require('semver');

class BreakingChangeAnalyzer {
  constructor(currentVersion, newVersion) {
    this.currentVersion = currentVersion;
    this.newVersion = newVersion;
    this.breakingChanges = [];
  }

  analyzeTokenChanges(currentTokens, newTokens) {
    const changes = {
      removed: [],
      renamed: [],
      valueChanged: [],
      typeChanged: []
    };

    // Check for removed tokens
    Object.keys(currentTokens).forEach(key => {
      if (!newTokens[key]) {
        changes.removed.push(key);
        this.breakingChanges.push({
          type: 'token_removed',
          token: key,
          impact: 'high',
          migration: `Replace usage of ${key} with alternative token`
        });
      }
    });

    // Check for value changes that might break layouts
    Object.keys(newTokens).forEach(key => {
      if (currentTokens[key] && currentTokens[key] !== newTokens[key]) {
        const currentValue = currentTokens[key];
        const newValue = newTokens[key];
        
        // Check if it's a significant change
        if (this.isSignificantChange(currentValue, newValue)) {
          changes.valueChanged.push({ key, currentValue, newValue });
          this.breakingChanges.push({
            type: 'token_value_changed',
            token: key,
            impact: 'medium',
            migration: `Review usage of ${key} - value changed from ${currentValue} to ${newValue}`
          });
        }
      }
    });

    return changes;
  }

  analyzeComponentChanges(currentComponents, newComponents) {
    const changes = {
      removed: [],
      apiChanged: [],
      propsChanged: []
    };

    // Analyze component API changes
    Object.keys(currentComponents).forEach(componentName => {
      const currentComponent = currentComponents[componentName];
      const newComponent = newComponents[componentName];

      if (!newComponent) {
        changes.removed.push(componentName);
        this.breakingChanges.push({
          type: 'component_removed',
          component: componentName,
          impact: 'high',
          migration: `Replace ${componentName} with alternative component`
        });
        return;
      }

      // Check for prop changes
      const propChanges = this.analyzePropChanges(
        currentComponent.props,
        newComponent.props
      );

      if (propChanges.length > 0) {
        changes.propsChanged.push({ componentName, changes: propChanges });
        propChanges.forEach(change => {
          this.breakingChanges.push({
            type: 'component_prop_changed',
            component: componentName,
            prop: change.prop,
            impact: change.impact,
            migration: change.migration
          });
        });
      }
    });

    return changes;
  }

  generateMigrationGuide() {
    if (this.breakingChanges.length === 0) {
      return null;
    }

    const guide = {
      version: this.newVersion,
      breakingChanges: this.breakingChanges,
      migrationSteps: this.generateMigrationSteps(),
      automatedMigration: this.generateAutomatedMigration()
    };

    return guide;
  }

  isSignificantChange(currentValue, newValue) {
    // Check if numeric values changed significantly
    const currentNum = parseFloat(currentValue);
    const newNum = parseFloat(newValue);
    
    if (!isNaN(currentNum) && !isNaN(newNum)) {
      const percentChange = Math.abs((newNum - currentNum) / currentNum);
      return percentChange > 0.1; // 10% change threshold
    }

    // For non-numeric values, any change is significant
    return currentValue !== newValue;
  }

  analyzePropChanges(currentProps, newProps) {
    const changes = [];

    // Check for removed props
    Object.keys(currentProps).forEach(prop => {
      if (!newProps[prop]) {
        changes.push({
          type: 'removed',
          prop,
          impact: 'high',
          migration: `Remove ${prop} prop or use alternative`
        });
      }
    });

    // Check for type changes
    Object.keys(newProps).forEach(prop => {
      if (currentProps[prop] && currentProps[prop].type !== newProps[prop].type) {
        changes.push({
          type: 'type_changed',
          prop,
          impact: 'medium',
          migration: `Update ${prop} prop type from ${currentProps[prop].type} to ${newProps[prop].type}`
        });
      }
    });

    return changes;
  }

  generateMigrationSteps() {
    const steps = [];
    
    this.breakingChanges.forEach((change, index) => {
      steps.push({
        step: index + 1,
        description: change.migration,
        impact: change.impact,
        automated: this.canAutomate(change)
      });
    });

    return steps;
  }

  generateAutomatedMigration() {
    const automatedChanges = this.breakingChanges.filter(change => 
      this.canAutomate(change)
    );

    if (automatedChanges.length === 0) {
      return null;
    }

    return {
      script: 'migrate-design-system.js',
      changes: automatedChanges,
      instructions: 'Run `npm run migrate:design-system` to apply automated migrations'
    };
  }

  canAutomate(change) {
    // Define which changes can be automated
    const automatableTypes = [
      'token_renamed',
      'component_prop_renamed',
      'simple_value_change'
    ];

    return automatableTypes.includes(change.type);
  }
}

module.exports = BreakingChangeAnalyzer;
```

### 3. Stakeholder Communication

#### Pre-Deployment Notification Template

```markdown
# Design System Update Notification

## Deployment Details
- **Version**: v2.1.0
- **Scheduled Deployment**: [Date and Time]
- **Expected Duration**: 30 minutes
- **Environments**: Staging → Production

## Changes Summary
### New Features
- Enhanced underwater theme animations
- New component variants for data visualization
- Improved accessibility features

### Improvements
- Updated color palette for better contrast
- Optimized component performance
- Enhanced responsive behavior

### Breaking Changes
- ⚠️ Deprecated `oldButton` component (use `Button` instead)
- ⚠️ Updated spacing tokens (see migration guide)

## Impact Assessment
- **User Impact**: Minimal - visual improvements only
- **Developer Impact**: Medium - migration required for deprecated components
- **Performance Impact**: Positive - 15% bundle size reduction

## Migration Required
- [ ] Update deprecated component usage
- [ ] Review custom CSS using updated tokens
- [ ] Test responsive layouts

## Resources
- [Migration Guide](link-to-migration-guide)
- [Updated Documentation](link-to-docs)
- [Support Channel](link-to-support)

## Rollback Plan
If issues are detected, we will immediately rollback to v2.0.5 within 15 minutes.

## Contact
For questions or concerns, contact the Design System team at design-system@aquachain.com
```

## Deployment Procedures

### 1. Staging Deployment

#### Automated Staging Pipeline

```bash
#!/bin/bash
# deploy-staging.sh

set -e

echo "🚀 Starting Design System Staging Deployment"

# Validate pre-deployment requirements
echo "🔍 Running pre-deployment validation..."
./scripts/validate-design-tokens.sh
./scripts/validate-components.sh
./scripts/validate-documentation.sh

# Build design system package
echo "🏗️ Building design system package..."
npm run build:design-system

# Deploy to staging environment
echo "📦 Deploying to staging..."
npm run deploy:staging

# Wait for deployment to complete
echo "⏳ Waiting for deployment to stabilize..."
sleep 30

# Run smoke tests
echo "🧪 Running staging smoke tests..."
npm run test:smoke:staging

# Run accessibility tests
echo "♿ Running accessibility validation..."
npm run test:a11y:staging

# Run performance tests
echo "⚡ Running performance validation..."
npm run test:performance:staging

# Run visual regression tests
echo "👁️ Running visual regression tests..."
npm run test:visual:staging

# Generate staging report
echo "📊 Generating staging validation report..."
npm run generate:staging-report

echo "✅ Staging deployment complete!"
echo "📋 Review staging report: https://staging.aquachain.com/design-system-report"
```

#### Staging Validation Checklist

```markdown
## Staging Validation Checklist

### Functional Testing
- [ ] All components render correctly
- [ ] Interactive elements function properly
- [ ] Form validation works as expected
- [ ] Navigation flows complete successfully
- [ ] Error states display appropriately

### Visual Testing
- [ ] Design tokens applied correctly
- [ ] Color palette displays properly
- [ ] Typography renders consistently
- [ ] Spacing and layout appear correct
- [ ] Animations perform smoothly

### Accessibility Testing
- [ ] WCAG 2.1 AA compliance verified
- [ ] Keyboard navigation functional
- [ ] Screen reader compatibility confirmed
- [ ] Color contrast meets requirements
- [ ] Focus indicators visible

### Performance Testing
- [ ] Bundle size within acceptable limits
- [ ] Page load times meet targets
- [ ] Component render performance optimal
- [ ] Memory usage stable
- [ ] No performance regressions detected

### Cross-Browser Testing
- [ ] Chrome functionality verified
- [ ] Firefox compatibility confirmed
- [ ] Safari rendering correct
- [ ] Edge behavior validated
- [ ] Mobile browsers tested

### Integration Testing
- [ ] Design system integrates with main application
- [ ] Third-party components work correctly
- [ ] API integrations function properly
- [ ] State management operates correctly
- [ ] Routing behavior validated
```

### 2. Production Deployment

#### Blue-Green Deployment Strategy

```bash
#!/bin/bash
# deploy-production.sh

set -e

echo "🚀 Starting Production Deployment (Blue-Green)"

# Configuration
BLUE_ENV="production-blue"
GREEN_ENV="production-green"
CURRENT_ENV=$(get-current-production-env)
TARGET_ENV=$(get-target-env $CURRENT_ENV)

echo "📋 Deployment Configuration:"
echo "  Current Environment: $CURRENT_ENV"
echo "  Target Environment: $TARGET_ENV"
echo "  Design System Version: $(get-package-version)"

# Pre-deployment validation
echo "🔍 Running final pre-deployment validation..."
npm run validate:production-ready

# Deploy to target environment
echo "🚀 Deploying to $TARGET_ENV..."
deploy-to-environment $TARGET_ENV

# Wait for deployment to complete
echo "⏳ Waiting for deployment to stabilize..."
wait-for-deployment $TARGET_ENV

# Run comprehensive validation
echo "🧪 Running production validation suite..."
npm run test:production:comprehensive -- --env=$TARGET_ENV

# Validate performance metrics
echo "⚡ Validating performance metrics..."
validate-performance-metrics $TARGET_ENV

# Run security scan
echo "🔒 Running security validation..."
npm run security:scan -- --env=$TARGET_ENV

# Validate accessibility compliance
echo "♿ Validating accessibility compliance..."
npm run test:a11y:production -- --env=$TARGET_ENV

# Check for any critical issues
if check-critical-issues $TARGET_ENV; then
  echo "❌ Critical issues detected. Aborting deployment."
  exit 1
fi

# Switch traffic to new environment
echo "🔄 Switching traffic to $TARGET_ENV..."
switch-production-traffic $TARGET_ENV

# Monitor for issues
echo "📊 Monitoring deployment for 10 minutes..."
monitor-deployment $TARGET_ENV 600

# Verify deployment success
if verify-deployment-success $TARGET_ENV; then
  echo "✅ Production deployment successful!"
  
  # Clean up old environment
  echo "🧹 Cleaning up previous environment..."
  cleanup-environment $CURRENT_ENV
  
  # Send success notification
  send-deployment-notification "success" $TARGET_ENV
else
  echo "❌ Deployment verification failed. Initiating rollback..."
  rollback-deployment $CURRENT_ENV
  exit 1
fi
```

#### Production Deployment Checklist

```markdown
## Production Deployment Checklist

### Pre-Deployment
- [ ] Staging validation completed successfully
- [ ] Breaking change analysis completed
- [ ] Migration guide prepared and reviewed
- [ ] Stakeholder notification sent
- [ ] Rollback plan confirmed
- [ ] Monitoring alerts configured
- [ ] Support team notified

### Deployment Execution
- [ ] Blue-green deployment initiated
- [ ] Target environment deployment completed
- [ ] Smoke tests passed
- [ ] Performance metrics validated
- [ ] Security scan completed
- [ ] Accessibility compliance verified
- [ ] Traffic switch executed
- [ ] Monitoring activated

### Post-Deployment
- [ ] User experience monitoring active
- [ ] Error rates within normal range
- [ ] Performance metrics stable
- [ ] No critical issues reported
- [ ] Documentation updated
- [ ] Team notification sent
- [ ] Deployment tagged in version control

### Rollback Criteria
- [ ] Error rate increase >5%
- [ ] Performance degradation >10%
- [ ] Critical accessibility failures
- [ ] Security vulnerabilities detected
- [ ] User-reported critical issues
```

### 3. Canary Deployment (Alternative Strategy)

```bash
#!/bin/bash
# deploy-canary.sh

set -e

echo "🐤 Starting Canary Deployment"

# Deploy to small percentage of users
echo "🚀 Deploying to 5% of users..."
deploy-canary 5

# Monitor for 30 minutes
echo "📊 Monitoring canary deployment..."
monitor-canary 1800

if check-canary-health; then
  echo "✅ Canary healthy. Increasing to 25%..."
  deploy-canary 25
  monitor-canary 1800
  
  if check-canary-health; then
    echo "✅ Canary stable. Increasing to 50%..."
    deploy-canary 50
    monitor-canary 1800
    
    if check-canary-health; then
      echo "✅ Canary successful. Rolling out to 100%..."
      deploy-canary 100
      echo "🎉 Canary deployment complete!"
    else
      echo "❌ Canary failed at 50%. Rolling back..."
      rollback-canary
    fi
  else
    echo "❌ Canary failed at 25%. Rolling back..."
    rollback-canary
  fi
else
  echo "❌ Canary failed at 5%. Rolling back..."
  rollback-canary
fi
```

## Rollback Procedures

### 1. Automated Rollback Triggers

```javascript
// rollback-monitor.js
class RollbackMonitor {
  constructor(config) {
    this.config = config;
    this.metrics = new MetricsCollector();
    this.alerting = new AlertingService();
  }

  startMonitoring(deploymentId) {
    const monitoringInterval = setInterval(() => {
      this.checkMetrics(deploymentId);
    }, this.config.checkInterval);

    // Stop monitoring after deployment window
    setTimeout(() => {
      clearInterval(monitoringInterval);
    }, this.config.monitoringDuration);
  }

  async checkMetrics(deploymentId) {
    const metrics = await this.metrics.getCurrentMetrics();
    
    // Check error rate
    if (metrics.errorRate > this.config.thresholds.errorRate) {
      await this.triggerRollback(deploymentId, 'high_error_rate', metrics.errorRate);
      return;
    }

    // Check performance degradation
    if (metrics.responseTime > this.config.thresholds.responseTime) {
      await this.triggerRollback(deploymentId, 'performance_degradation', metrics.responseTime);
      return;
    }

    // Check accessibility failures
    if (metrics.accessibilityScore < this.config.thresholds.accessibilityScore) {
      await this.triggerRollback(deploymentId, 'accessibility_failure', metrics.accessibilityScore);
      return;
    }

    // Check user experience metrics
    if (metrics.userSatisfaction < this.config.thresholds.userSatisfaction) {
      await this.triggerRollback(deploymentId, 'user_experience_degradation', metrics.userSatisfaction);
      return;
    }
  }

  async triggerRollback(deploymentId, reason, metric) {
    console.log(`🚨 Triggering automatic rollback: ${reason} (${metric})`);
    
    // Send immediate alert
    await this.alerting.sendCriticalAlert({
      type: 'automatic_rollback',
      deploymentId,
      reason,
      metric,
      timestamp: new Date().toISOString()
    });

    // Execute rollback
    await this.executeRollback(deploymentId);
  }

  async executeRollback(deploymentId) {
    try {
      // Get previous stable version
      const previousVersion = await this.getPreviousStableVersion();
      
      // Execute rollback
      await this.deploymentService.rollback(previousVersion);
      
      // Verify rollback success
      const rollbackSuccess = await this.verifyRollback(previousVersion);
      
      if (rollbackSuccess) {
        await this.alerting.sendAlert({
          type: 'rollback_success',
          deploymentId,
          rolledBackTo: previousVersion,
          timestamp: new Date().toISOString()
        });
      } else {
        await this.alerting.sendCriticalAlert({
          type: 'rollback_failed',
          deploymentId,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      await this.alerting.sendCriticalAlert({
        type: 'rollback_error',
        deploymentId,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
}
```

### 2. Manual Rollback Procedure

```bash
#!/bin/bash
# manual-rollback.sh

set -e

ROLLBACK_VERSION=$1

if [ -z "$ROLLBACK_VERSION" ]; then
  echo "❌ Rollback version required"
  echo "Usage: ./manual-rollback.sh <version>"
  echo "Available versions:"
  list-available-versions
  exit 1
fi

echo "🔄 Starting manual rollback to version $ROLLBACK_VERSION"

# Verify rollback version exists
if ! verify-version-exists $ROLLBACK_VERSION; then
  echo "❌ Version $ROLLBACK_VERSION not found"
  exit 1
fi

# Confirm rollback
echo "⚠️  This will rollback the design system to version $ROLLBACK_VERSION"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Rollback cancelled"
  exit 1
fi

# Execute rollback
echo "🚀 Rolling back to version $ROLLBACK_VERSION..."
deploy-version $ROLLBACK_VERSION

# Wait for rollback to complete
echo "⏳ Waiting for rollback to complete..."
wait-for-deployment-complete

# Verify rollback success
echo "🔍 Verifying rollback success..."
if verify-rollback-success $ROLLBACK_VERSION; then
  echo "✅ Rollback successful!"
  
  # Send notification
  send-rollback-notification $ROLLBACK_VERSION
  
  # Update monitoring
  update-monitoring-version $ROLLBACK_VERSION
else
  echo "❌ Rollback verification failed"
  exit 1
fi
```

## Post-Deployment Procedures

### 1. Monitoring and Validation

```bash
#!/bin/bash
# post-deployment-monitoring.sh

echo "📊 Starting post-deployment monitoring..."

# Monitor for 2 hours
MONITORING_DURATION=7200
START_TIME=$(date +%s)

while [ $(($(date +%s) - START_TIME)) -lt $MONITORING_DURATION ]; do
  # Check system health
  if ! check-system-health; then
    echo "❌ System health check failed"
    trigger-alert "system_health_failure"
  fi
  
  # Check performance metrics
  if ! check-performance-metrics; then
    echo "⚠️ Performance metrics degraded"
    trigger-alert "performance_degradation"
  fi
  
  # Check error rates
  if ! check-error-rates; then
    echo "❌ Error rates elevated"
    trigger-alert "high_error_rate"
  fi
  
  # Check user feedback
  if ! check-user-feedback; then
    echo "⚠️ Negative user feedback detected"
    trigger-alert "user_feedback_negative"
  fi
  
  # Wait before next check
  sleep 300 # 5 minutes
done

echo "✅ Post-deployment monitoring complete"
```

### 2. Documentation Updates

```bash
#!/bin/bash
# update-documentation.sh

echo "📚 Updating documentation..."

# Update version in documentation
update-documentation-version

# Generate changelog
generate-changelog

# Update component documentation
update-component-docs

# Update migration guides
update-migration-guides

# Rebuild documentation site
build-documentation-site

# Deploy documentation updates
deploy-documentation

echo "✅ Documentation updated successfully"
```

### 3. Team Communication

#### Post-Deployment Report Template

```markdown
# Design System Deployment Report

## Deployment Summary
- **Version**: v2.1.0
- **Deployment Date**: [Date]
- **Deployment Duration**: 45 minutes
- **Status**: ✅ Successful

## Metrics
### Performance
- Bundle Size: 245KB (-15% from previous)
- Load Time: 1.2s (target: <2.5s)
- Core Web Vitals: All green

### Quality
- Test Coverage: 85%
- Accessibility Score: 98%
- Zero critical issues detected

### User Impact
- Error Rate: 0.02% (normal range)
- User Satisfaction: 4.2/5.0
- Support Tickets: No increase

## Changes Deployed
### New Features
- ✨ Enhanced underwater animations
- ✨ New data visualization components
- ✨ Improved mobile responsiveness

### Bug Fixes
- 🐛 Fixed color contrast issues
- 🐛 Resolved keyboard navigation problems
- 🐛 Corrected spacing inconsistencies

### Breaking Changes
- ⚠️ Deprecated `OldButton` component
- ⚠️ Updated spacing token values

## Migration Status
- **Components Migrated**: 45/50 (90%)
- **Remaining Work**: 5 components need migration
- **Timeline**: Complete by [Date]

## Next Steps
1. Complete remaining component migrations
2. Monitor user feedback for 1 week
3. Plan next iteration based on feedback
4. Update team training materials

## Resources
- [Updated Documentation](link)
- [Migration Guide](link)
- [Support Channel](link)

## Team Recognition
Special thanks to the design and development teams for their excellent work on this release!
```

## Maintenance Procedures

### 1. Regular Health Checks

```bash
#!/bin/bash
# design-system-health-check.sh

echo "🏥 Running Design System Health Check..."

# Check token consistency
echo "🎨 Checking design token consistency..."
npm run validate:tokens:consistency

# Check component API stability
echo "🧩 Checking component API stability..."
npm run validate:component-apis

# Check documentation accuracy
echo "📚 Checking documentation accuracy..."
npm run validate:documentation

# Check accessibility compliance
echo "♿ Checking accessibility compliance..."
npm run test:a11y:full

# Check performance benchmarks
echo "⚡ Checking performance benchmarks..."
npm run test:performance:benchmark

# Generate health report
echo "📊 Generating health report..."
npm run generate:health-report

echo "✅ Health check complete"
```

### 2. Dependency Management

```bash
#!/bin/bash
# update-dependencies.sh

echo "📦 Updating design system dependencies..."

# Update npm dependencies
npm update

# Check for security vulnerabilities
npm audit

# Update peer dependencies
npm run update:peer-dependencies

# Run tests after updates
npm run test:full

# Update lock file
npm install

echo "✅ Dependencies updated successfully"
```

### 3. Performance Optimization

```bash
#!/bin/bash
# optimize-performance.sh

echo "⚡ Optimizing design system performance..."

# Analyze bundle size
npm run analyze:bundle

# Optimize assets
npm run optimize:assets

# Tree-shake unused code
npm run optimize:tree-shake

# Compress and minify
npm run build:optimized

# Validate performance improvements
npm run test:performance:compare

echo "✅ Performance optimization complete"
```

## Emergency Procedures

### 1. Critical Issue Response

```markdown
## Critical Issue Response Plan

### Severity Levels
- **P0 (Critical)**: System down, security breach, data loss
- **P1 (High)**: Major functionality broken, accessibility failures
- **P2 (Medium)**: Minor functionality issues, performance degradation
- **P3 (Low)**: Cosmetic issues, documentation errors

### Response Times
- **P0**: Immediate response (within 15 minutes)
- **P1**: Within 1 hour
- **P2**: Within 4 hours
- **P3**: Within 24 hours

### Escalation Path
1. On-call engineer
2. Design system team lead
3. Engineering manager
4. CTO (for P0 issues)

### Communication Channels
- **Internal**: Slack #design-system-alerts
- **External**: Status page updates
- **Stakeholders**: Email notifications
```

### 2. Hotfix Deployment

```bash
#!/bin/bash
# deploy-hotfix.sh

HOTFIX_VERSION=$1

if [ -z "$HOTFIX_VERSION" ]; then
  echo "❌ Hotfix version required"
  exit 1
fi

echo "🚨 Deploying critical hotfix $HOTFIX_VERSION"

# Skip normal validation for critical fixes
echo "⚠️ Skipping extended validation for hotfix"

# Build hotfix
npm run build:hotfix

# Deploy directly to production
npm run deploy:hotfix:production -- $HOTFIX_VERSION

# Monitor closely
npm run monitor:hotfix -- $HOTFIX_VERSION

echo "✅ Hotfix deployed. Monitoring for issues..."
```

This comprehensive deployment procedure ensures safe, reliable, and well-monitored rollouts of design system updates while providing clear processes for handling issues and maintaining system health.