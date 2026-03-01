#!/bin/bash

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🎯 Katyayani Organics - Final GitHub Deployment Check      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

# Check syntax
echo "📝 Checking Python syntax..."
if python3 -m py_compile main.py continuous_chat.py config.py 2>/dev/null; then
    echo "   ✓ All files compile successfully"
    PASSED=$((PASSED+1))
else
    echo "   ✗ Syntax errors found"
    FAILED=$((FAILED+1))
fi

# Check setup.sh exists
echo "📝 Checking deployment files..."
FILES=("Procfile" "Dockerfile" "docker-compose.yml" "runtime.txt" "setup.sh" ".github/workflows/deploy.yml")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
        PASSED=$((PASSED+1))
    else
        echo "   ✗ $file missing"
        FAILED=$((FAILED+1))
    fi
done

# Check .env exists
echo "📝 Checking configuration..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    PASSED=$((PASSED+1))
else
    echo "   ✗ .env file missing (will ask for it)"
fi

# Check documentation
echo "📝 Checking documentation..."
DOCS=("QUICKSTART.md" "DOCUMENTATION.md" "DEPLOY_GUIDE.md" "PRODUCTION_CHECKLIST.md" "READY_FOR_GITHUB.md")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✓ $doc"
        PASSED=$((PASSED+1))
    else
        echo "   ✗ $doc missing"
        FAILED=$((FAILED+1))
    fi
done

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   📊 FINAL REPORT                                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "   ✓ Passed: $PASSED"
echo "   ✗ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "   ✅ Ready for GitHub Deployment!"
    echo ""
    echo "   🚀 Next steps:"
    echo "      1. git add ."
    echo "      2. git commit -m 'Katyayani Bot - Gemini AI Auto-Chat Ready'"
    echo "      3. git push origin main"
    echo ""
    echo "   💡 GitHub Actions will auto-test and deploy!"
    exit 0
else
    echo "   ❌ Fix the issues above before deploying"
    exit 1
fi
