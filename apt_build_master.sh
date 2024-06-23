#!/bin/bash

# Function to display the menu
show_menu() {
    clear
    echo
    echo "=============================================================="
    echo "                      AplusTools Main Menu"
    echo "=============================================================="
    echo "1.             Install pytest and run tests"
    echo "2.                 Clear dist directory"
    echo "3.                  Build the project"
    echo "4.           Install the newly built package"
    echo "5. Run all steps in order (1, 2, 3 & 4)"
    echo "0. Exit"
    echo "=============================================================="
    echo
    read -p "Enter your choice (0-5, or multiple choices): " choice
    process_choice
}

# Function to process the choice
process_choice() {
    local len=${#choice}
    for (( i=0; i<$len; i++ )); do
        local opt=${choice:i:1}
        case $opt in
            1) run_tests ;;
            2) clear ;;
            3) build_project ;;
            4) install_package ;;
            5) run_all ;;
            0) end ;;
            *) echo "Invalid choice: $opt" ;;
        esac
    done
    pause
    end
}

# Function to process the choice without pause
process_choice_no_pause() {
    local len=${#choice}
    for (( i=0; i<$len; i++ )); do
        local opt=${choice:i:1}
        case $opt in
            1) run_tests ;;
            2) clear ;;
            3) build_project ;;
            4) install_package ;;
            5) run_all ;;
            0) end ;;
            *) echo "Invalid choice: $opt" ;;
        esac
    done
    end
}

# Function to pause the script
pause() {
    read -p "Press any key to continue..." -n1 -s
}

# Function to run tests
run_tests() {
    # Install pytest
    python3 -m pip install pytest

    # Ensure test_data directory exists and is empty
    DIR="test_data"
    if [ -d "$DIR" ]; then
        echo "Clearing directory $DIR..."
        rm -rf "$DIR"
    fi
    echo "Creating directory $DIR..."
    mkdir "$DIR"

    # Run tests
    echo "Running tests..."
    python3 -m pytest src/aplustools/tests
    echo "Tests completed."
}

# Function to build the project
build_project() {
    # Install build
    python3 -m pip install build
    echo "Building the project..."
    python3 -m build
    echo "Build completed."
}

# Function to clear dist directory and build
clear() {
    echo "Clearing dist directory..."
    rm -rf dist/*
}

# Function to install the newly built package
install_package() {
    for file in dist/*.whl; do
        python3 -m pip install "$file"[all] --force-reinstall
    done
    echo "Package installation completed."
}

# Function to run all steps
run_all() {
    run_tests
    build_project
    install_package
}

# Function to end the script
end() {
    echo "Exiting..."
    exit 0
}

# Command line arguments processing
if [ -n "$1" ]; then
    choice=$1
    process_choice_no_pause
else
    show_menu
fi
