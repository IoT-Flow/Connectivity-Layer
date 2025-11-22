# Requirements Document - IoT Dashboard Frontend

## Introduction

This document specifies the requirements for a web-based IoT Dashboard frontend that enables users to monitor and manage their IoT devices. The dashboard provides device management, real-time telemetry visualization through charts, and user authentication with role-based access control. The system integrates with an existing Flask backend API that manages devices, telemetry data, and user authentication.

## Glossary

- **Dashboard**: The main web application interface for monitoring and managing IoT devices
- **Device**: An IoT hardware unit (sensor, actuator, etc.) that sends telemetry data to the platform
- **Telemetry**: Time-series measurement data sent by devices (temperature, humidity, pressure, etc.)
- **Chart**: A saved configuration for visualizing telemetry data from one or multiple devices with specific settings
- **Chart Configuration**: The saved settings for a chart including name, type, time range, devices, and measurements
- **Chart Type**: The visualization format (line chart, bar chart, or area chart)
- **ChartDevice**: A database association linking a chart to one or more devices
- **ChartMeasurement**: A database record defining which measurements to display in a chart with display names and colors
- **User**: A person with an account who owns and manages devices
- **Admin**: A user with elevated privileges who can view all users and all devices
- **API Key**: A unique authentication token generated for each device upon registration
- **Status**: The current operational state of a device (online, offline, active, inactive, maintenance)
- **Measurement**: A specific data point type from a device (e.g., temperature, humidity)
- **Time Range**: A period for filtering telemetry data (Last Hour, Last 24 Hours, Last 7 Days, Last 30 Days)

## Requirements

### Requirement 1: User Authentication and Authorization

**User Story:** As a user, I want to log in to the dashboard so that I can securely access my devices and data.

#### Acceptance Criteria

1. WHEN a user navigates to the dashboard URL, THE Dashboard SHALL display a login page
2. WHEN a user submits valid credentials, THE Dashboard SHALL authenticate the user via the backend API and grant access to the main interface
3. WHEN a user submits invalid credentials, THE Dashboard SHALL display an error message and remain on the login page
4. WHEN a user is authenticated, THE Dashboard SHALL store the authentication token securely for subsequent API requests
5. WHEN a user logs out, THE Dashboard SHALL clear the authentication token and redirect to the login page

### Requirement 2: User Registration

**User Story:** As a new user, I want to register an account so that I can start using the IoT platform.

#### Acceptance Criteria

1. WHEN a user clicks the registration link on the login page, THE Dashboard SHALL display a registration form
2. WHEN a user submits the registration form with valid data, THE Dashboard SHALL create a new user account via the backend API
3. WHEN registration is successful, THE Dashboard SHALL redirect the user to the login page with a success message
4. WHEN registration fails due to duplicate username or email, THE Dashboard SHALL display an appropriate error message
5. THE Dashboard SHALL validate that required fields (username, email, password) are provided before submission

### Requirement 3: Device List Display

**User Story:** As a logged-in user, I want to see a list of my devices so that I can monitor their status at a glance.

#### Acceptance Criteria

1. WHEN a user logs in successfully, THE Dashboard SHALL display the main page with a table of the user's devices
2. THE Dashboard SHALL display the following columns in the device table: Device Name, Type, Status, Last Seen, and Actions
3. WHEN a device is online, THE Dashboard SHALL display the status with a visual indicator (e.g., green color or icon)
4. WHEN a device is offline, THE Dashboard SHALL display the status with a different visual indicator (e.g., red color or icon)
5. THE Dashboard SHALL fetch device data from the backend API endpoint `/api/v1/devices/user/{user_id}`

### Requirement 4: Device Registration from Dashboard

**User Story:** As a user, I want to register new devices from the dashboard so that I can easily add devices to my account.

#### Acceptance Criteria

1. WHEN a user clicks the "Add Device" button, THE Dashboard SHALL display a device registration form
2. THE Dashboard SHALL provide input fields for device name, description, device type, location, firmware version, and hardware version
3. WHEN a user submits the registration form with valid data, THE Dashboard SHALL send a POST request to `/api/v1/devices/register`
4. WHEN device registration is successful, THE Dashboard SHALL display the generated API key in a modal or alert
5. THE Dashboard SHALL provide a way to copy the API key to clipboard and warn that it will not be shown again

### Requirement 5: Device Details and Chart Visualization

**User Story:** As a user, I want to view detailed information and telemetry charts for a specific device so that I can monitor its performance over time.

#### Acceptance Criteria

1. WHEN a user clicks the "View" action button for a device, THE Dashboard SHALL navigate to a device details page
2. THE Dashboard SHALL display device information at the top of the page including name, type, status, location, firmware version, hardware version, and last seen timestamp
3. THE Dashboard SHALL display a single chart showing all measurement types (temperature, humidity, pressure, etc.) with different colored lines
4. THE Dashboard SHALL fetch telemetry data from the backend API endpoint `/api/v1/telemetry/{device_id}`
5. WHEN no telemetry data exists for the device, THE Dashboard SHALL display a message indicating no data is available

### Requirement 6: Chart Time Range Filtering

**User Story:** As a user, I want to filter chart data by time range so that I can analyze device performance over different periods.

#### Acceptance Criteria

1. THE Dashboard SHALL provide preset time range buttons: "Last Hour", "Last 24 Hours", "Last 7 Days", and "Last 30 Days"
2. WHEN a user clicks a time range button, THE Dashboard SHALL fetch telemetry data for the selected time period
3. THE Dashboard SHALL send the appropriate `start_time` parameter to the backend API based on the selected time range
4. WHEN the time range changes, THE Dashboard SHALL update the chart to display data for the new time period
5. THE Dashboard SHALL indicate which time range is currently selected with visual feedback (e.g., highlighted button)

### Requirement 7: Manual Chart Refresh

**User Story:** As a user, I want to manually refresh the chart data so that I can see the latest telemetry readings.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a "Refresh" button on the device details page
2. WHEN a user clicks the "Refresh" button, THE Dashboard SHALL fetch the latest telemetry data from the backend API
3. WHEN new data is received, THE Dashboard SHALL update the chart to display the refreshed data
4. THE Dashboard SHALL provide visual feedback during the refresh operation (e.g., loading spinner)
5. THE Dashboard SHALL NOT automatically refresh chart data without user interaction

### Requirement 8: Device Editing

**User Story:** As a user, I want to edit device information so that I can keep device details up to date.

#### Acceptance Criteria

1. WHEN a user clicks the "Edit" action button for a device, THE Dashboard SHALL display an edit form with current device information
2. THE Dashboard SHALL allow editing of device name, description, location, firmware version, and hardware version
3. WHEN a user submits the edit form, THE Dashboard SHALL send a PUT request to `/api/v1/devices/{device_id}`
4. WHEN the update is successful, THE Dashboard SHALL display a success message and update the device list
5. WHEN the update fails, THE Dashboard SHALL display an error message with details

### Requirement 9: Device Deletion

**User Story:** As a user, I want to delete devices so that I can remove devices that are no longer in use.

#### Acceptance Criteria

1. WHEN a user clicks the "Delete" action button for a device, THE Dashboard SHALL display a confirmation dialog
2. THE Dashboard SHALL require explicit confirmation before proceeding with deletion
3. WHEN a user confirms deletion, THE Dashboard SHALL send a DELETE request to `/api/v1/devices/{device_id}`
4. WHEN deletion is successful, THE Dashboard SHALL remove the device from the list and display a success message
5. WHEN deletion fails, THE Dashboard SHALL display an error message and keep the device in the list

### Requirement 10: Admin User Management

**User Story:** As an admin user, I want to view and manage all users in the system so that I can administer the platform.

#### Acceptance Criteria

1. WHEN an admin user logs in, THE Dashboard SHALL display an additional "Users" navigation option
2. WHEN an admin clicks the "Users" option, THE Dashboard SHALL display a list of all users in the system
3. THE Dashboard SHALL fetch user data from the backend API endpoint `/api/v1/admin/users` or `/api/v1/users`
4. THE Dashboard SHALL display user information including username, email, account status, and registration date
5. WHERE the user is an admin, THE Dashboard SHALL provide options to view user details and manage user accounts

### Requirement 11: Admin Device Management

**User Story:** As an admin user, I want to view all devices in the system regardless of owner so that I can monitor the entire platform.

#### Acceptance Criteria

1. WHEN an admin user views the device list, THE Dashboard SHALL display all devices from all users
2. THE Dashboard SHALL fetch device data from the backend API endpoint `/api/v1/admin/devices`
3. THE Dashboard SHALL display the device owner's username in the device list for admin users
4. WHERE the user is an admin, THE Dashboard SHALL allow viewing and managing any device in the system
5. THE Dashboard SHALL clearly indicate which devices belong to which users in the admin view

### Requirement 12: Responsive Design

**User Story:** As a user, I want the dashboard to work on different screen sizes so that I can access it from various devices.

#### Acceptance Criteria

1. THE Dashboard SHALL display correctly on desktop screens (1920x1080 and above)
2. THE Dashboard SHALL display correctly on tablet screens (768px to 1024px width)
3. THE Dashboard SHALL display correctly on mobile screens (320px to 767px width)
4. WHEN the screen size changes, THE Dashboard SHALL adapt the layout to maintain usability
5. THE Dashboard SHALL ensure that all interactive elements remain accessible on smaller screens

### Requirement 13: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when operations succeed or fail so that I understand what is happening.

#### Acceptance Criteria

1. WHEN an API request fails, THE Dashboard SHALL display an error message with relevant details
2. WHEN an operation succeeds, THE Dashboard SHALL display a success message
3. WHEN data is loading, THE Dashboard SHALL display a loading indicator
4. THE Dashboard SHALL handle network errors gracefully and inform the user
5. THE Dashboard SHALL provide actionable error messages that help users resolve issues

### Requirement 14: Light Theme Visual Design

**User Story:** As a user, I want a clean and minimal light-themed interface so that the dashboard is easy to read and professional.

#### Acceptance Criteria

1. THE Dashboard SHALL use a light color scheme with white or light gray backgrounds
2. THE Dashboard SHALL use appropriate contrast ratios for text readability
3. THE Dashboard SHALL use consistent spacing, typography, and visual hierarchy
4. THE Dashboard SHALL use color coding for status indicators (green for online, red for offline, yellow for maintenance)
5. THE Dashboard SHALL maintain a clean and minimal aesthetic throughout all pages

### Requirement 15: Chart Management Page

**User Story:** As a user, I want to create and manage custom charts so that I can visualize telemetry data from one or multiple devices with specific configurations.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a "Charts" page accessible from the main navigation
2. WHEN a user navigates to the Charts page, THE Dashboard SHALL display a list of all charts created by the user
3. THE Dashboard SHALL provide a "Create Chart" button on the Charts page
4. WHEN a user clicks "Create Chart", THE Dashboard SHALL display a chart creation form
5. THE Dashboard SHALL fetch the user's saved charts from the backend API endpoint `/api/v1/charts?user_id={user_id}`

### Requirement 16: Chart Creation

**User Story:** As a user, I want to create custom charts with specific configurations so that I can monitor the exact data I need.

#### Acceptance Criteria

1. THE Dashboard SHALL provide input fields for chart name, description, chart type, and time range in the chart creation form
2. THE Dashboard SHALL allow users to select one or multiple devices to include in the chart
3. THE Dashboard SHALL allow users to select which measurements to display (temperature, humidity, pressure, etc.)
4. THE Dashboard SHALL support chart types: line, bar, and area
5. WHEN a user submits the chart creation form, THE Dashboard SHALL send a POST request to `/api/v1/charts` with the chart configuration

### Requirement 17: Chart Configuration Storage

**User Story:** As a user, I want my chart configurations saved so that I can view them again later with the same settings.

#### Acceptance Criteria

1. WHEN a chart is created, THE Dashboard SHALL save the chart configuration to the Chart table via the backend API
2. THE Dashboard SHALL save device associations to the ChartDevice table for each selected device
3. THE Dashboard SHALL save measurement configurations to the ChartMeasurement table for each selected measurement
4. THE Dashboard SHALL assign a unique color to each measurement in the ChartMeasurement table
5. WHEN chart creation is successful, THE Dashboard SHALL display a success message and redirect to the Charts page

### Requirement 18: Viewing Saved Charts

**User Story:** As a user, I want to view my saved charts so that I can monitor my devices with my preferred configurations.

#### Acceptance Criteria

1. WHEN a user clicks on a saved chart from the Charts page, THE Dashboard SHALL display the chart with the saved configuration
2. THE Dashboard SHALL fetch chart details from `/api/v1/charts/{chart_id}` including associated devices and measurements
3. THE Dashboard SHALL fetch telemetry data from `/api/v1/charts/{chart_id}/data` based on the saved time range
4. THE Dashboard SHALL display the chart using the saved chart type (line, bar, or area)
5. THE Dashboard SHALL use the saved colors for each measurement line

### Requirement 19: Chart Editing

**User Story:** As a user, I want to edit my saved charts so that I can update configurations as my needs change.

#### Acceptance Criteria

1. WHEN a user clicks an "Edit" button on a saved chart, THE Dashboard SHALL display the chart configuration form with current settings
2. THE Dashboard SHALL allow modifying chart name, description, chart type, time range, devices, and measurements
3. WHEN a user submits the edit form, THE Dashboard SHALL send a PUT request to `/api/v1/charts/{chart_id}`
4. WHEN the update is successful, THE Dashboard SHALL display a success message and refresh the chart view
5. THE Dashboard SHALL update the ChartDevice and ChartMeasurement tables if devices or measurements are changed

### Requirement 20: Chart Deletion

**User Story:** As a user, I want to delete charts I no longer need so that I can keep my Charts page organized.

#### Acceptance Criteria

1. WHEN a user clicks a "Delete" button on a saved chart, THE Dashboard SHALL display a confirmation dialog
2. THE Dashboard SHALL require explicit confirmation before proceeding with deletion
3. WHEN a user confirms deletion, THE Dashboard SHALL send a DELETE request to `/api/v1/charts/{chart_id}`
4. WHEN deletion is successful, THE Dashboard SHALL remove the chart from the list and display a success message
5. THE Dashboard SHALL cascade delete associated ChartDevice and ChartMeasurement records

### Requirement 21: Multi-Device Chart Visualization

**User Story:** As a user, I want to view data from multiple devices on a single chart so that I can compare device performance.

#### Acceptance Criteria

1. WHEN a chart includes multiple devices, THE Dashboard SHALL fetch telemetry data for all associated devices
2. THE Dashboard SHALL display measurement data from all devices on the same chart
3. THE Dashboard SHALL differentiate between devices using labels or visual indicators
4. WHEN multiple devices have the same measurement type, THE Dashboard SHALL display them as separate lines with different colors
5. THE Dashboard SHALL provide a legend showing which line corresponds to which device and measurement

### Requirement 22: Navigation and Layout

**User Story:** As a user, I want intuitive navigation so that I can easily move between different sections of the dashboard.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a navigation bar or sidebar with links to main sections: Devices, Charts, and Settings
2. THE Dashboard SHALL display the current user's username and a logout button in the navigation area
3. WHEN a user clicks a navigation link, THE Dashboard SHALL navigate to the corresponding page
4. THE Dashboard SHALL indicate the current active page in the navigation
5. WHERE the user is an admin, THE Dashboard SHALL display additional navigation options for Users and admin features
