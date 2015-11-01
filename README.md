# slackrollpy
Simple implementation of a slack client for python based dice rolling bot using RTM.

#### Installing

Depends on slack client for python.

https://github.com/slackhq/python-slackclient

Edit the flags in slackroll.py -- you can also change the default messaging here if you'd like. Add your slack token and default channel to slacktoken.py.

#### Using the roller

The syntax is pretty straightforward. Use __roll__ or __roll help__ to get help. In the basic "roll" command the minimum parameter is "#ds" with # being the number to roll and s being the number of sides, ie, _roll 3d6_ would roll three six-sided dice. You can also specify __target num__ or __t num__ to set a target difficulty (anything lower than _num_ is a failure, equal to or above is a success). For example, _roll 7d10t8_ rolls seven ten-sided dice, and any at eight or above are considered successes. Exploding dice are indicated with __explode num__ or __e num__ (anything equal to or above _num_ will be rerolled until it is no longer above, potentially giving multiple results per die rolled). For example, _roll 7d10t8e10_ would roll seven ten-sided dice, rerolling any tens until they are less than ten, and considering anything equal to or over eight to be a success.

You can use the shorthand __nwod num__ to roll using the default paramters for New World of Darkness (ten sided dice, target 8, roll again on 10). _nwod 7_ is equivalent to _roll7d10t8e10_.

Finally, you can add the keyword __rote__ to any command with a specified target number to reroll any failed rolls once. For example, _roll 7d10t8e10 rote_.

#### To Add

    Reign/ORE style matches
    Percentile dice
