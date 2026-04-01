#!/usr/bin/env sh

BUMP="${1:?Usage: release.sh <major|minor|patch>}"
LATEST=$(git fetch && git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
MAJOR=$(echo "$LATEST" | cut -d. -f1)
MINOR=$(echo "$LATEST" | cut -d. -f2)
PATCH=$(echo "$LATEST" | cut -d. -f3)
case "$BUMP" in
	major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
	minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
	patch) PATCH=$((PATCH + 1)) ;;
	*) echo "Invalid BUMP value: $BUMP. Use major, minor, or patch." && exit 1 ;;
esac;
VERSION="$MAJOR.$MINOR.$PATCH"
echo "Tagging release $VERSION (was $LATEST)"
git tag -a "$VERSION" -m "Release $VERSION"
echo "Tag $VERSION created. Push with: git push origin $VERSION"
