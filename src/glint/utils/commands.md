# Glint CLI Commands Documentation

This document lists all available commands for the Glint CLI.

## Core Commands

### `init`
Initializes the Glint database.
- **Usage**: `glint init`
- **Description**: Creates the SQLite database file and initializes all necessary tables. Run this first after installation.

### `add`
Adds a new topic to your watch list.
- **Usage**: `glint add <topic_name>`
- **Example**: `glint add python`
- **Description**: Adds a topic. Glint will fetch trends related to this topic.

### `list`
Lists all watched topics.
- **Usage**: `glint list`
- **Description**: Displays a table of all topics you are currently watching, along with their active status.

### `fetch`
Manually triggers a trend fetch.
- **Usage**: `glint fetch`
- **Description**: Connects to configured sources (GitHub, Hacker News) and fetches the latest trends for your active topics.

### `status`
Displays the system status.
- **Usage**: `glint status`
- **Description**: Shows statistics like total topics, total trends, unread count, database size, and last fetch time.

### `clear`
Clears the terminal screen.
- **Usage**: `glint clear`
- **Description**: Clears the output in the system terminal or the Glint GUI terminal.

## Configuration Commands (`config`)

### `config topics list`
Lists all topics with their status.
- **Usage**: `glint config topics list`
- **Description**: Same as `glint list`, shows active/inactive status.

### `config topics toggle`
Toggles a topic's active status.
- **Usage**: `glint config topics toggle <topic_name>`
- **Example**: `glint config topics toggle python`
- **Description**: Enables or disables a topic without deleting it. Inactive topics are skipped during fetch.

### `config topics delete`
Deletes a topic permanently.
- **Usage**: `glint config topics delete <topic_name>`
- **Example**: `glint config topics delete java`
- **Description**: Removes the topic from your watch list.

### `config schedule set`
Sets the notification time window.
- **Usage**: `glint config schedule set <start_time> <end_time>`
- **Format**: HH:MM (24-hour format)
- **Example**: `glint config schedule set 09:00 18:00`
- **Description**: Configures Glint to only send system notifications between these hours.

### `config schedule show`
Shows the current notification schedule.
- **Usage**: `glint config schedule show`
- **Description**: Displays the currently configured start and end times for notifications.
