# Contributing to ATIS

Thank you for your interest in contributing to the Automated Threat Intelligence System (ATIS)! This guide will help you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, trolling, or derogatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 16+ (for frontend tools)
- Git
- Docker (optional but recommended)

### Fork and Clone
```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/atis.git
cd atis

# Add upstream remote
git remote add upstream https://github.com/original/atis.git
```

## Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 4. Initialize Database (Optional)
```bash
# Using Docker
docker-compose up -d postgres redis

# Or install PostgreSQL/Redis locally
```

### 5. Run Development Server
```bash
uvicorn src.web.main:app --reload
```

Visit `http://localhost:8000` to see the application.

## How to Contribute

### Ways to Contribute
1. **Report Bugs**: Open an issue with detailed reproduction steps
2. **Suggest Features**: Propose new features via issues
3. **Fix Issues**: Look for "good first issue" labels
4. **Improve Documentation**: Fix typos, clarify instructions
5. **Write Tests**: Increase code coverage
6. **Review Pull Requests**: Help review other contributors' code

### Finding an Issue
- Check [open issues](https://github.com/original/atis/issues)
- Look for labels:
  - `good first issue` - Great for newcomers
  - `help wanted` - Extra attention needed
  - `bug` - Something isn't working
  - `enhancement` - New feature or request

## Coding Standards

### Python Style Guide
We follow [PEP 8](https://pep8.org/) with some modifications:

```python
# Good: Clear, documented, typed
def calculate_threat_score(
    asteroid_data: np.ndarray,
    model: torch.nn.Module
) -> float:
    """
    Calculate threat score for an asteroid.
    
    Args:
        asteroid_data: Orbital parameters
        model: Trained GNN model
    
    Returns:
        Threat score between 0 and 1
    """
    # Implementation here
    pass
```

### JavaScript/HTML/CSS
- Use 2 spaces for indentation
- Use camelCase for JavaScript variables
- Use kebab-case for CSS classes
- Add accessibility attributes (ARIA)
- Write semantic HTML

### Code Quality Tools
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/

# Type check
mypy src/

# Run all checks
make lint  # (if Makefile exists)
```

## Testing

### Writing Tests
```python
# tests/test_threat_engine.py
import pytest
from src.risk.threat_engine import compute_threat_scores

def test_threat_score_range():
    """Threat scores should be between 0 and 1"""
    scores = compute_threat_scores(mock_data, mock_model)
    assert all(0 <= score <= 1 for score in scores)
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_threat_engine.py

# Run specific test
pytest tests/test_threat_engine.py::test_threat_score_range
```

### Test Coverage Goals
- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Pull Request Process

### 1. Create a Branch
```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-awesome-feature

# Or bug fix branch
git checkout -b fix/bug-description
```

### 2. Make Changes
- Write clear, descriptive commit messages
- Keep commits atomic and focused
- Follow coding standards

### 3. Commit Guidelines
```bash
# Good commit messages
git commit -m "feat: Add real-time WebSocket notifications"
git commit -m "fix: Correct threat score calculation for edge cases"
git commit -m "docs: Update API documentation with new endpoints"
git commit -m "test: Add unit tests for analytics engine"

# Follow Conventional Commits format:
# <type>(<scope>): <description>
#
# Types: feat, fix, docs, style, refactor, test, chore
```

### 4. Push and Create PR
```bash
# Push to your fork
git push origin feature/my-awesome-feature

# Create Pull Request on GitHub
```

### 5. PR Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
- [ ] PR description is clear

### 6. PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Screenshots (if applicable)

## Checklist
- [ ] Code follows guidelines
- [ ] Self-reviewed
- [ ] Commented complex parts
- [ ] Updated documentation
- [ ] Added tests
- [ ] All tests pass
```

## Issue Guidelines

### Reporting Bugs
Use the bug report template:

```markdown
**Describe the bug**
A clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment:**
 - OS: [e.g. Windows 11]
 - Browser: [e.g. Chrome 120]
 - Version: [e.g. 1.0.0]

**Additional context**
Any other information
```

### Feature Requests
Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Any other information or mockups
```

## Development Workflow

### Typical Development Cycle
1. Pick an issue
2. Comment on the issue to claim it
3. Create feature branch
4. Write code
5. Write tests
6. Run tests locally
7. Commit changes
8. Push to fork
9. Create pull request
10. Address review feedback
11. Merge!

### Code Review Process
- At least one maintainer approval required
- All CI checks must pass
- Address all review comments
- Keep discussions professional and constructive

## Additional Resources

### Documentation
- [API Documentation](https://your-domain.com/docs)
- [Architecture Overview](docs/architecture.md)
- [Deployment Guide](DEPLOYMENT.md)

### Communication
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Email: contribute@atis.local

### Learning Resources
- [PyTorch Geometric Tutorial](https://pytorch-geometric.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [NASA APIs](https://api.nasa.gov/)

## Recognition

### Contributors
All contributors will be:
- Added to the `CONTRIBUTORS.md` file
- Credited in release notes
- Part of the ATIS community 🚀

Thank you for contributing to planetary defense! Every contribution, no matter how small, helps protect Earth. 🌍
