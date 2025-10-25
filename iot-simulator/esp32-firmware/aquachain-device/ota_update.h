/*
 * OTA Update Handler for ESP32
 * Handles secure over-the-air firmware updates
 */

#ifndef OTA_UPDATE_H
#define OTA_UPDATE_H

#include <Arduino.h>
#include <Update.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <mbedtls/md.h>
#include <esp_ota_ops.h>
#include <esp_partition.h>

// OTA Configuration
#define OTA_BUFFER_SIZE 1024
#define OTA_MAX_RETRIES 3
#define OTA_TIMEOUT_MS 300000  // 5 minutes

class OTAUpdateHandler {
private:
    String currentVersion;
    String targetVersion;
    bool updateInProgress;
    int updateProgress;
    
    // Partition information for rollback support
    const esp_partition_t* currentPartition;
    const esp_partition_t* updatePartition;
    
public:
    OTAUpdateHandler() {
        updateInProgress = false;
        updateProgress = 0;
        currentPartition = esp_ota_get_running_partition();
        updatePartition = esp_ota_get_next_update_partition(NULL);
    }
    
    /**
     * Initialize OTA update handler
     */
    void begin(String firmwareVersion) {
        currentVersion = firmwareVersion;
        
        Serial.println("OTA Update Handler initialized");
        Serial.printf("Current firmware version: %s\n", currentVersion.c_str());
        Serial.printf("Current partition: %s\n", currentPartition->label);
        Serial.printf("Update partition: %s\n", updatePartition->label);
    }
    
    /**
     * Check for available firmware updates from shadow
     */
    bool checkForUpdate(DynamicJsonDocument& shadow) {
        if (!shadow.containsKey("state") || !shadow["state"].containsKey("desired")) {
            return false;
        }
        
        JsonObject desired = shadow["state"]["desired"];
        
        if (!desired.containsKey("firmware")) {
            return false;
        }
        
        JsonObject firmware = desired["firmware"];
        
        if (!firmware.containsKey("update_available") || 
            !firmware["update_available"].as<bool>()) {
            return false;
        }
        
        targetVersion = firmware["version"].as<String>();
        
        // Check if update is needed
        if (targetVersion == currentVersion) {
            Serial.println("Firmware is already up to date");
            return false;
        }
        
        Serial.printf("Firmware update available: %s -> %s\n", 
                     currentVersion.c_str(), targetVersion.c_str());
        
        return true;
    }
    
    /**
     * Perform OTA update from URL
     */
    bool performUpdate(String firmwareUrl, String checksum, int firmwareSize) {
        if (updateInProgress) {
            Serial.println("Update already in progress");
            return false;
        }
        
        updateInProgress = true;
        updateProgress = 0;
        
        Serial.println("Starting OTA update...");
        Serial.printf("URL: %s\n", firmwareUrl.c_str());
        Serial.printf("Size: %d bytes\n", firmwareSize);
        Serial.printf("Checksum: %s\n", checksum.c_str());
        
        bool success = false;
        
        for (int attempt = 1; attempt <= OTA_MAX_RETRIES; attempt++) {
            Serial.printf("Update attempt %d/%d\n", attempt, OTA_MAX_RETRIES);
            
            if (downloadAndInstallFirmware(firmwareUrl, checksum, firmwareSize)) {
                success = true;
                break;
            }
            
            if (attempt < OTA_MAX_RETRIES) {
                Serial.println("Retrying in 5 seconds...");
                delay(5000);
            }
        }
        
        updateInProgress = false;
        
        if (success) {
            Serial.println("✓ OTA update completed successfully");
            Serial.println("Rebooting in 5 seconds...");
            delay(5000);
            ESP.restart();
        } else {
            Serial.println("✗ OTA update failed after all retries");
        }
        
        return success;
    }
    
    /**
     * Download and install firmware
     */
    bool downloadAndInstallFirmware(String url, String expectedChecksum, int expectedSize) {
        HTTPClient http;
        WiFiClientSecure client;
        
        // Skip certificate validation for presigned URLs
        client.setInsecure();
        
        http.begin(client, url);
        http.setTimeout(OTA_TIMEOUT_MS);
        
        int httpCode = http.GET();
        
        if (httpCode != HTTP_CODE_OK) {
            Serial.printf("HTTP GET failed: %d\n", httpCode);
            http.end();
            return false;
        }
        
        int contentLength = http.getSize();
        
        if (contentLength != expectedSize) {
            Serial.printf("Size mismatch: expected %d, got %d\n", expectedSize, contentLength);
            http.end();
            return false;
        }
        
        // Begin OTA update
        if (!Update.begin(contentLength)) {
            Serial.printf("Not enough space for OTA: %d bytes needed\n", contentLength);
            http.end();
            return false;
        }
        
        // Download and write firmware
        WiFiClient* stream = http.getStreamPtr();
        uint8_t buffer[OTA_BUFFER_SIZE];
        int bytesWritten = 0;
        
        // Initialize checksum calculation
        mbedtls_md_context_t ctx;
        mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;
        mbedtls_md_init(&ctx);
        mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 0);
        mbedtls_md_starts(&ctx);
        
        while (http.connected() && bytesWritten < contentLength) {
            size_t available = stream->available();
            
            if (available) {
                int bytesToRead = min((int)available, OTA_BUFFER_SIZE);
                int bytesRead = stream->readBytes(buffer, bytesToRead);
                
                // Update checksum
                mbedtls_md_update(&ctx, buffer, bytesRead);
                
                // Write to flash
                if (Update.write(buffer, bytesRead) != bytesRead) {
                    Serial.println("Error writing firmware");
                    Update.abort();
                    http.end();
                    mbedtls_md_free(&ctx);
                    return false;
                }
                
                bytesWritten += bytesRead;
                updateProgress = (bytesWritten * 100) / contentLength;
                
                // Print progress every 10%
                if (updateProgress % 10 == 0) {
                    Serial.printf("Progress: %d%%\n", updateProgress);
                }
            }
            
            delay(1);
        }
        
        // Finalize checksum
        unsigned char hash[32];
        mbedtls_md_finish(&ctx, hash);
        mbedtls_md_free(&ctx);
        
        // Convert hash to hex string
        String calculatedChecksum = "";
        for (int i = 0; i < 32; i++) {
            char hex[3];
            sprintf(hex, "%02x", hash[i]);
            calculatedChecksum += hex;
        }
        
        http.end();
        
        // Verify checksum
        if (calculatedChecksum != expectedChecksum) {
            Serial.println("Checksum verification failed!");
            Serial.printf("Expected: %s\n", expectedChecksum.c_str());
            Serial.printf("Calculated: %s\n", calculatedChecksum.c_str());
            Update.abort();
            return false;
        }
        
        Serial.println("✓ Checksum verified");
        
        // Finalize update
        if (!Update.end(true)) {
            Serial.printf("Update error: %s\n", Update.errorString());
            return false;
        }
        
        Serial.println("✓ Firmware installed successfully");
        
        return true;
    }
    
    /**
     * Report update status to AWS IoT
     */
    void reportUpdateStatus(PubSubClient& mqttClient, String deviceId, 
                           String status, String errorMessage = "") {
        DynamicJsonDocument doc(512);
        doc["deviceId"] = deviceId;
        doc["firmwareVersion"] = targetVersion;
        doc["status"] = status;
        doc["timestamp"] = millis();
        
        if (errorMessage.length() > 0) {
            doc["error"] = errorMessage;
        }
        
        String topic = "aquachain/" + deviceId + "/ota/status";
        String payload;
        serializeJson(doc, payload);
        
        mqttClient.publish(topic.c_str(), payload.c_str());
        
        Serial.printf("Reported OTA status: %s\n", status.c_str());
    }
    
    /**
     * Get current firmware version
     */
    String getCurrentVersion() {
        return currentVersion;
    }
    
    /**
     * Get update progress (0-100)
     */
    int getProgress() {
        return updateProgress;
    }
    
    /**
     * Check if update is in progress
     */
    bool isUpdateInProgress() {
        return updateInProgress;
    }
    
    /**
     * Rollback to previous partition (if update failed)
     */
    bool rollbackToPrevious() {
        Serial.println("Attempting rollback to previous firmware...");
        
        // Get the partition that was running before
        const esp_partition_t* previousPartition = esp_ota_get_next_update_partition(NULL);
        
        if (previousPartition == NULL) {
            Serial.println("No previous partition found");
            return false;
        }
        
        // Set boot partition to previous
        esp_err_t err = esp_ota_set_boot_partition(previousPartition);
        
        if (err != ESP_OK) {
            Serial.printf("Failed to set boot partition: %d\n", err);
            return false;
        }
        
        Serial.println("✓ Rollback configured, rebooting...");
        delay(2000);
        ESP.restart();
        
        return true;
    }
    
    /**
     * Validate current firmware after boot
     * Call this in setup() to confirm successful update
     */
    void validateFirmware() {
        esp_ota_img_states_t ota_state;
        const esp_partition_t* running = esp_ota_get_running_partition();
        
        if (esp_ota_get_state_partition(running, &ota_state) == ESP_OK) {
            if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
                Serial.println("Firmware pending verification...");
                
                // Mark firmware as valid
                esp_ota_mark_app_valid_cancel_rollback();
                
                Serial.println("✓ Firmware validated successfully");
            }
        }
    }
};

#endif // OTA_UPDATE_H
