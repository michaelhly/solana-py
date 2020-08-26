rm -rf docs _build
make docs
git checkout gh-pages
shopt -s extglob
git rm -- !(docs)
touch docs/.nojekyll
git push origin gh-pages
echo current branch:
git branch
