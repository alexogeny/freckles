#!/bin/bash

# Store the original username
ORIGINAL_USER=$(logname)

# Define the sudoers file path
SUDOERS_FILE="/etc/sudoers.d/$ORIGINAL_USER"

# Switch to root using 'su'
su -c "bash -c \"echo '# Granting sudo privileges to the original user' > $SUDOERS_FILE; \
echo '$ORIGINAL_USER ALL=(ALL:ALL) ALL' >> $SUDOERS_FILE; \
chmod 0440 $SUDOERS_FILE\""
