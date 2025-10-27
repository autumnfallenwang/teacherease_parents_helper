#!/bin/bash
# TeacherEase Parents Helper - Daily Runner Script

# Change to project directory
cd /home/aaronwang/github/teacherease_parents_helper

# Run with uv
/home/aaronwang/.local/bin/uv run python main.py

# Exit with the same status code
exit $?
