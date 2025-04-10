#!/bin/bash

# Set colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No color

echo "Starting to check for placeholder paths in configuration files..."

# List of files to check - add more files as needed
FILES_TO_CHECK=(
  "mcp_servers/servers_config.json"
  ".env"
)

found_placeholders=false

for file in "${FILES_TO_CHECK[@]}"; do
  if [ -f "$file" ]; then
    # Look for lines containing "/your" or "/path/to/your"
    placeholders=$(grep -n "/your" "$file" || true)
    
    if [ -n "$placeholders" ]; then
      found_placeholders=true
      echo -e "${RED}Found unmodified paths in file $file:${NC}"
      echo "$placeholders"
      echo ""
    else
      echo -e "${GREEN}File $file is correctly configured, no placeholder paths found.${NC}"
    fi
  else
    echo -e "${RED}Warning: File $file does not exist, cannot check.${NC}"
  fi
done

if [ "$found_placeholders" = true ]; then
  echo -e "${RED}Please modify the placeholder paths in the above files to your actual paths.${NC}"
  exit 1
else
  echo -e "${GREEN}All checked files are correctly configured!${NC}"
  exit 0
fi