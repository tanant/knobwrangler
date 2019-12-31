## Overview
Nuke knobs can be a bit of a pain, they're hard to wrangle and there's no clean API to do things programatically. I've written this module probably three times now, independently, when it's gotten too annoying to do singlehandledly, so i think it's now time to actually just do it

### Specs! Design decisions
(This is an abbreviated high level spec doc, but you know, good form)
This module will provide fucntions for:
- add, remove, insert operations
- bulk operations (invisible/uninvisible, flag setting, etc)

Anything you can do here:
- should match the UI, that includes name mangling!
- GUI and nonGUI operation should be identical as well


### What Nuke version? (11.3v5)
This is all being tested/built against Nuke 11.3v5 as (current) mainline. Any deviation to behaviour for Nuke 10 will be considered either as bugfix/backport feature OR if it's behaviour mimickry - the Nuke 11 behaviour will be considered 'right'


### Docs
Currently docs are all inline - it's assumed (rightly or wrongly) if you're using this module you're familiar enough with Nuke's knob paradigms that the code here will sort of more or less work as you'd expect.


### Contributions / Issues
Feel free to add issues to the list and make PRs against them (or wait for me to do the fixes, either or)


### Distribution / packging
Right now this is a barebones python file, but I'll do some wrapping into an egg at some stage.


### Tests
Ah yeah. This this module is tightly bound to Nuke as a platform alas, and you will need to inject it into the nuke interpreter in the pythonpath

As this purely relates to knobs, you can actually use nuke NC for tests as necessary the way I've written this. Assuming that you don't have a better way to bootstrap, you can use the `bootstrap.py` script, for example if you're in windows..:

```
&"C:\Program Files\Nuke11.3v5\Nuke11.3.exe" --nc -t E:\repos\knobwrangler\tests\bootstrap.py  -v
```
