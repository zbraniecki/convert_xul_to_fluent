This is an attempt to develop a script that aids Firefox migration to Fluent.

Installing:

```
pip3 install -r requirements.txt
```

Example usage (taken from https://bugzilla.mozilla.org/show_bug.cgi?id=1592043):

```
# If the FTL file doesn't exist yet:
touch ~/Code/mozilla-central/devtools/client/locales/en-US/toolbox.ftl

python3 convert.py --bug_id 1592043 --description "Migrate toolbox options strings from DTD to FTL" --mc ~/Code/mozilla-central --dom devtools/client/framework/toolbox-options.xhtml --dtd devtools/client/locales/en-US/toolbox.dtd --ftl devtools/client/locales/en-US/toolbox.ftl
```
