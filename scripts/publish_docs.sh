git checkout gh-pages
rm -rf docs _build
git fetch origin master
git pull origin master
make docs
touch docs/.nojekyll
git add docs
git commit -m "Publish docs"
git push origin gh-pages
rm -rf docs
echo branches:
git branch
