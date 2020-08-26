rm -rf docs _build
git checkout gh-pages
git fetch origin master
git pull origin master
make docs
shopt -s extglob
git rm -- !(docs)
touch docs/.nojekyll
git push origin gh-pages
echo current branch:
git branch
