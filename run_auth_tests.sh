#!/bin/bash
pytest tests/test_auth.py -v > /tmp/auth_tests_result.txt 2>&1
echo "Tests completed with exit code: $?"