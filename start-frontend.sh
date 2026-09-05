#!/bin/bash
set -e

cd "$(dirname "$0")/frontend/nextjs"
exec npm run dev
