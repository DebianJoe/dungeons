This document contains a small write up to help new and less experienced users to get the dungeons project running on their machine.

The first section focusses on just getting `dungeons.py` to run.

The second section shortly explains how to use github to make changes and push them back to the online code repository. 

1. With Git
-----------

Git allows you to easily update your game code in the future.

This will setup game files to live in `~/games/dungeons`. You are welcome to change this path to fit your needs.

Open a terminal and run:

	# install git
	sudo apt-get install git

	# enter the games directory
	mkdir -p ~/games && cd ~/games

	# clone the code
	# this will create a sub directory "dungeons"
	git clone https://github.com/DebianJoe/dungeons.git

	# in a later time to update the local copy based on what other people changed in git
	git pull

2. Without Git
--------------

Steps for those who want a direct download approach. You will need to do this each time you want to get a new version of the game.

This will setup game files to live in `~/games/dungeons`. You are welcome to change this path to fit your needs. The download link to the zip file is for the `master` branch.

Open a terminal and run:

	mkdir -p ~/games && cd ~/games
	wget -O dungeons.zip https://github.com/DebianJoe/dungeons/archive/master.zip
	unzip dungeons.zip && mv dungeons-master dungeons

3. Download the pre-requisite dependencies
------------------------------------------

* Grab version 1.5.1 from [http://doryen.eptalys.net/libtcod/download/](http://doryen.eptalys.net/libtcod/download/)
* Extract some place, it will create a subdirectory "libtcod-1.5.1"
* Copy the following two files from the extracted archive to the dungeons directory
  * libtcodpy.py
  * libtcod.so

I had some difficulty with libtcod.so on Crunchbang Waldorf 64. There is an [incident on DebinaJoes github](https://github.com/DebianJoe/dungeons/issues/1) that provides some more info in case you need it. 

4. Download the media files
--------------------------

* Grab the font: [http://postimg.org/image/a44ny3vgv](http://postimg.org/image/a44ny3vgv)
* Grab the background image: [http://postimg.org/image/dblayu895](http://postimg.org/image/dblayu895)
* Copy both to your dungeons directory

5. Run it
----------

Start the application from the dungeons directory

	python dungeons.py

6. To contribute
----------------

Please note this is not a full doc on Github. It is some notes I took when first setting this up and which might help first time Github users to get through it a bit quicker.

If you skipped part 1, make sure you do step 3 and step 4 to get the prerequired library libtcod and the media files.

6.1 Register & setup git
------------------------

Go to [GitHub.com](https://github.com), register an account.

Git is pre-installed on crunchbang but you need to configure it to use your newly created account, [steps are detailed here](https://help.github.com/articles/set-up-git](https://help.github.com/articles/set-up-git).

6.2 Fork DebianJoes repository
------------------------------

Next step is to create your own copy of the dungeons code, this is called a "fork", [steps are detailed here](https://help.github.com/articles/fork-a-repo).

I'll provide a bit more detail on how to apply it to the dungeons project. Note that all the git commands below have to be executed in the dugeons directory.

In short this is what should be done, replace <USERNAME> with your GitHub username!

On the github website: Log in and navigate to DebianJoes repository, click on the button fork (top right hand corner of main page). This will create a copy of the code (a fork) in your github account.

To download the code to your machine (this will create a subdirectory dungeons):

	git clone git@github.com:<USERNAME>/dungeons.git

Create upstream link to DebianJoes repository, you need this to be able to move your changes upstream back to DebianJoes master repository:

	cd dungeons
	git remote add upstream https://github.com/DebianJoe/dungeons.git

6.3 Make changes and upload them
--------------------------------

Change one of the local files, for example add your name to the README or tweak something in dungeons.py.

The files are now only changed locally. A this point it is perfectly normal that you break something. Before moving to the next step make sure you fix things so that they work :-)

Don't be afraid to experiment, if you completely break it you can "reset" your local version easily using git checkout. For example resetting the README file:

	git checkout -- README

Once you are happy with your changes you have to commit them. This confirms the changes in your own local github repository.

Commit all files, replace "comment here" with a short comment that describes your changes.

	git commit -am 'comment here'

_Note: You can omit the -m parameter, in this case you will get prompted for a comment by your CLI $EDITOR._

Next step is to push the changes out to your personnal git repository, for this use the push command:

	git push origin master.

You should see the changed file being uploaded, now your changes are in your github repository

How can you get the changes in the master version (DebianJoes repository)? Since DebianJoe is managing this repository you need to request him to pull in the changes from your repository. He is kinda like a gatekeeper. :-)

Do this via the Github website: Go to your repository and click on the Pull Request button. Fill in the little form and send it. This should result in a Pull request (yours) that shows up in DebianJoes repository where he can then treat it.

[More information about pull requests](https://help.github.com/articles/using-pull-requests/).

6.4 Get future changes from DebianJoes master repository
--------------------------------------------------------

Before starting work it is often a good idea to refresh your local files so you have the latests updates from the master repository.

First get upstream changes (we set upstream to point to DebianJoes repository in step 6.2)

	git fetch upstream
	
Then merge them in your repository

	git merge upstream/master
	
At this point the changes are local to your system. To push them in your own Github repository you can again use

	git push origin master

6.5 Branching
-------------

Branching allows you to hack new features or experimental code without touching the master code base. You can easily switch between your hacking branch, and the master branch. For an intro to branching see [here](http://git-scm.com/book/en/Git-Branching-Basic-Branching-and-Merging).

For the tl;dr here is the cheatsheet:

Create a local branch:

	git branch my-hack
	git checkout my-hack

In the my-hack branch you have a copy of the master. Hack away. You can switch back to the master (after commiting any changes):

	git checkout master

And switch back to your hacking branch:

	git checkout my-hack

This way you can hack multiple features each in their own copy of the code base.

When you are ready to push your branch up to GitHub for sharing:

	git checkout my-hack
	git push -u origin my-hack

This creates your my-hack branch in your fork on GitHub (if it does not exist). You can then use the "Pull Request" button on your GitHub repository to request your changes be reviewed and included in DebianJoe's code :-)
