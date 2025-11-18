#!/bin/bash
# Generate secure SECRET_KEY for production

echo "Generating secure SECRET_KEY..."
echo ""
echo "Add this to your .env file:"
echo ""
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo ""
echo "Or run this to update .env automatically:"
echo "sed -i 's/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/' .env"
