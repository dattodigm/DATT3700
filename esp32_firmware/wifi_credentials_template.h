/*
 * WiFi Credentials Template
 * 
 * Copy this file to wifi_config.h and update with your credentials
 * The wifi_config.h file is .gitignored to prevent accidental commits
 * 
 * Usage in flower_control.ino:
 * 1. Copy this file: cp wifi_credentials_template.h wifi_config.h
 * 2. Edit wifi_config.h with your actual credentials
 * 3. In flower_control.ino, replace lines 19-22 with: #include "wifi_config.h"
 */

#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

#endif
