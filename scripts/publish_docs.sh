rm -rf docs _build
git checkout gh-pages
git fetch origin master
git pull origin master
make docs
shopt -s extglob
git rm -rf !(docs)
shopt -u dotglob
touch docs/.nojekyll
git push origin gh-pages
echo branches:
git branch
