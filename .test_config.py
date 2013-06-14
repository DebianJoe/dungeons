#!/usr/bin/python

# This unit test will validate the dungeons.conf for syntax errors,
# invalid numbers and missing function names.
#
# It is recommended to run it before commiting any config changes:
#
# python .test_config.py

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import json
import random
import ConfigParser
import dungeons

def is_numeric(value):
    try:
        int(value)
    except ValueError:
        return False
    return True

def has_attrib(target, name):
    try:
        # if not name given we assume none was intended
        if len(name) > 1:
            getattr(target, name)
    except AttributeError:
        return False
    return True

if __name__ == '__main__':
    red = "\033[1;31m"
    green = "\033[1;32m"
    reset = "\033[1;m"
    print('\n# dungeons.conf unit test')
    print(random.choice(("analyzing air quality...",
        "calculating primordial soup...",
        "reading the future...",
        "carbon dating your hard drive...",
        "finding prime numbers...")))
    
    config = ConfigParser.ConfigParser()
    has_errors = False
    
    try:
        print('Loading dungeons.conf...')
        config.read('dungeons.conf')
    except Exception, e:
        print(red + str(e) + reset)
        sys.exit(1)
    
    for monster_name in config.get('lists', 'monster list').split(', '):
    
        # load this monster
        monster = dict(config.items(monster_name))
        
        print('\tTesting: %s...' % monster_name)
        
        try:
            json.loads(monster['chance'])
        except ValueError, e:
            has_errors = True
            print(red + '\t\tchance invalid' + reset)
        
        if not is_numeric(monster['hp']):
            has_errors = True
            print(red + '\t\thp is not numeric' + reset)
        if not is_numeric(monster['defense']):
            has_errors = True
            print(red + '\t\tdefense is not numeric' + reset)
        if not is_numeric(monster['power']):
            has_errors = True
            print(red + '\t\tpower is not numeric' + reset)
        if not is_numeric(monster['xp']):
            has_errors = True
            print(red + '\t\txp is not numeric' + reset)
        
        if not has_attrib(dungeons, monster['death_function']):
            has_errors = True
            print(red + '\t\tdeath_function invalid' + reset)
        if not has_attrib(dungeons, monster['ai_component']):
            has_errors = True
            print(red + '\t\tai_component invalid' + reset)
    if has_errors:
        print(red + 'Unit test failed' + reset)
    else:
        print(green + 'All systems go' + reset)
