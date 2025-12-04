#!/bin/bash
echo "Installing OpenRouter dependencies..."
cd api
pip uninstall google-generativeai -y
pip install openai==1.3.0
echo "OpenRouter setup complete!"
echo ""
echo "The app has been updated to use OpenRouter API instead of Gemini."
echo "Your API key is already configured in the .env file."
echo ""