#|/bin/bash
EXCLUDE="bin build develop-eggs eggs include lib local parts"
cd ..
cd ..
cd ..
~/bin/i18ndude rebuild-pot --pot genweb6/organs/locales/genweb6.organs.pot --create genweb6.organs . --exclude "$EXCLUDE"
cd genweb6/organs/locales/ca/LC_MESSAGES
~/bin/i18ndude sync --pot ../../genweb6.organs.pot genweb6.organs.po
cd ..
cd ..
cd en
cd LC_MESSAGES
~/bin/i18ndude sync --pot ../../genweb6.organs.pot genweb6.organs.po
cd ..
cd ..
cd es
cd LC_MESSAGES
~/bin/i18ndude sync --pot ../../genweb6.organs.pot genweb6.organs.po
