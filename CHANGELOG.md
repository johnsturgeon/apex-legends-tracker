# Changelog
Welcome to the 'Apex Legends Tracker' changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.21] - 2021-06-22
### Fixed
- Fixed exception being thrown in `save player` to log a warning now instead
  Resolves #197
- Fixed another exception being thrown in `save player` to log warning instead
  Resolves #199
  
## [1.2.20] - 2021-06-22
EMERGENCY FIX to the module paths

## [1.2.19] - 2021-06-22
This is a pretty massive change to the back end code, I'll detail a bit below:
## Changed
- Moved Event Player from Mashumaro to Pydantic
- Reduced dependencies between the DB Helper and the Model objects, I now just pass a DB into to the collection, and it 'does the right thing'
- Moved just a bit closer to making the db_helper class a simple storage object for the database connection Should always be passed to view controllers
- Continued to move domain specific knowledge into the object classes
- Split up the object model a bit for seasons and general 'config' information instead of a strange basic_info collection
- Simplified the season start / end / split dates (only one truth).
- Battlepass info comes from config
- Wrote more unit tests

## [1.2.18] - 2021-06-18
### Changed
- Moved the configuration information to be read from 'instance' folder
- Resolves #194
- Resolves #190

## [1.2.17] - 2021-06-18
### Fixed
- I'm now catching errors when connections go bad to the api server.
- Resolves #193

## [1.2.16] - 2021-06-17
### Fixed
- One more small deployment issue

## [1.2.14] - 2021-06-17
### Fixed
- Fixed deployment issue

## [1.2.13] - 2021-06-17
### Added
- Added a `begin` and `end` deployment scripts (Resolves #185)
- Fixed the 'start_tracker' script to not start if one is running already (Resolves #184)

## [1.2.12] - 2021-06-17
### Fixed
- Fixed a duplicate data bug (#182)
- Fixed the maintenance script location

## [1.2.11] - 2021-06-16
### Added
- Added meta-data tags for preview of site when pasting in iphone

## [1.2.10] - 2021-06-16
### Fixed
- Fixed the ranked progression page to show the split

## [1.2.9] - 2021-06-16
### Fixed
- Fixed an error that caused the scraper script to sometimes crash (#175)

## [1.2.8] - 2021-06-14
### Fixed
- Tweaked a bit of the 'range' calculation for finding games that are close to yours.
- Resolves #167

## [1.2.7] - 2021-06-14
Octane release: "Must. Go. Faster"

### Changed
- Moved to a new web host, faster, faster, faster

### Fixed
= Fixed script path

## [1.2.5] - 2021-06-12
### Changed
- Made a couple styling changes to the day detail page

## [1.2.3] - 2021-06-12
### Fixed
- Another Emergency Fix to module import

## [1.2.2] - 2021-06-12
### Fixed
- Another Emergency Fix to module import

## [1.2.1] - 2021-06-12
### Fixed
- Emergency Fix to module import

## [1.2.0] - 2021-06-12
### Added
- Added new 'Day Detail' page.  You can get there by clicking on your player profile, or using the main menu.
- Shows people you partied up with.  It might not be perfect, but it's pretty darned close.

### Changed
- Refactored a ton of the way that the model data is handled, this will make it much easier to make changes in the future

## [1.1.2] - 2021-06-10
- Resolves #158 (profile page has error when there are zero ranked games)

## [1.1.1]
### Fixed
- Fixed a lint issue by moving some code into a separate method.

## [1.1.0]
### Added
- Added 'distance to next tier' on the ranked progression page

## [1.0.2]
Emergency fix saving cookie

## [1.0.1]
### Fixed
- Fix for discord login
- Will now only prompt to log in every two weeks, and even then the auth process should be quicker
- Fixed 'claim my user' so that it will 'remember' your claim

## [1.0.0]
Introducing version 1.0.0!  I'm introducing the concept of 'login via discord' and 'claim your profile'
The way it works is that you will log in using your discord credentials, and then 'link' your profile to your discord account.
Once you've done that you will just log in, and be able to see all your data

## Added
- Discord login
- Claim profile

## Changed
- Nav bar to make a lot more sense

## [0.9.4]
Emergency fix for data scraping script
- Fixed it to use new Player object

## [0.9.3]
Internal updates only (no user facing differences)

### Changed
- Did away with 'player_data', I now just use the `Player` dataclass
- Updated the serialization to use `mashumaro` instead of `desert` (much better docs)

## [0.9.2]
### Changed
- Using a new method for accessing data models (dataclasses / desert JSON deserializer to dataclass)
- Changed the ranked progression page to use the 'game' data for ranked progression which means that the old data is now gone
- Fixed the battlepass tracker to max to 100 not 110

## [0.9.1]
### Added
- Hover labels on ranked progression page show some more detail (and are styled a bit)
- Added a 15-second refresh to the maintenance page to check to see if the site is ready, and if it is, reload it.
### Fixed
- Fixed the Rank Progression tracker page (several issues)
### Changed
- [internal change] moved some season / battlepass data into a config database

## [0.9.0]
### Added
- This is the final release for the ranked progression chart. 
To see your ranked progression for the current season you just go to your 'profile' page.

## [0.8.4]
More ranked progression work

## [0.8.3]
Prep work for saving ranked progression

## [0.8.2]
Various small bug fixes that have been bothering me.

### Changed
- Upgrade python packages
- Upgrade to Flask 2.0 (Resolves #104)
- Themed the `date picker` on the home page (Resolves #84)

## [0.8.1]
### Fixed
- Fixed it so that the home page no longer refreshes when it's not on 'Today'
- Moved the 'prev / next' date navigation into the content area of the home page, so we don't have two headers there.
- Resolves #125
### Added
- Added platform logo to the user's profile page (#122)

## [0.8.0]
### Added
- Added new `Battlepass Tracker` page (Issues #96)
### Fixed
- Changed the background color of the site so 'white' wouldn't bleed through any longer (Issue #120)

## [0.7.0]
Taking three steps backwards and one step forwards.
Pretty massive refactor here, I removed the tracker page since it was not quite right, and I really have to get it right, there are a lot of details with regards to the different kinds of trackers and how they can be reported, so I need to be a bit more deliberate before I bring it back.

### Removed
- Removed the trackers from the profile page
- Removed the tracker detail (when clicking on a tracker)
### Changed
- Changed the profile page so that it is kind of a dumbed down version of data that is not tracker data, mostly state data.  Plan is to add to this often and quickly
- Changed the default player link to go to their `day-to-day` page instead of their profile
### Fixed
- Fixed massive performance issues, anything I add from now on will be performant
- Fixed a home page refresh timing issue
- Fixed a javascript issue on the home page
- Speed improvements for the `day-to-day` page

## [0.6.0] - 2021-05-16
### Changed
- Redesigned Home Page!
  - More visual space
  - Sortable headers!
  - Still fast load time
  - Prev / Next for date selection
- Consistent Navigation Bar  
- Added a new `favicon`

## [0.5.5] - 2021-05-15
### Fixed
- Fixed multiple issues connecting to the database by migrating to MongoDB Atlas (cloud)

## [0.5.4] - 2021-05-13
### Added
- Added `WBR` to the `Day to Day` page
  WBR is calculated by `xp / games played / 100` and is intended to give you an idea about overall game effectiveness. 
  A higher `WBR` is better, from my initial investigation, a `WBR` of > 30 is kind of the benchmark for a good day
  NOTE: `WBR` stands for WarBlade Rating
  
## Fixed
- Fixed an issue with the legend tracker page not updating live.  This meant that in order for you 
  to see results in the tracker detail page you had to manually refresh your browser, that is no
  longer the case

## [0.5.3] - 2021-05-11
### Fixed
- Fixed a date/time issue when selecting previous / next days

## [0.5.2] - 2021-05-11
### Fixed
- EMERGENCY FIX: Fixed an issue with the wins total

## [0.5.1] - 2021-05-11
### Changed
- Performance improvement!  Front page now loads significantly faster, I'll be working on more performance improvements over time

## [0.5.0] - 2021-05-10
This is a pretty big release, I'm adding a kind of 'profile' stats page where you can see your
tracker totals for the trackers that are currently tracked.  Also provided is a new `tracker_detail`
page where you can go through your legends and enable trackers and get them up-to-date.

### Added
- Added `profile` page
  - Page will show you some basic tracker stats and a 'preview' of a damage tracking chart (more to come)
  - Click on a tracker to see all the legend by legend detail of the tracker
- Added `tracker detail` page
  - Tracker detail page is where you manage your tracker data.  This is a special new page that will walk you through the process of making sure your trackers are up to date
- Added a navigation header (not very good right now, super manual)

### Changed
- Moved the 'day by day' page to a link off the main page
- Clicking on a player from the leaderboard will bring you to their profile page, and not the day-by-day page an more


## [0.4.7] - 2021-05-09
### Added
- Added startup / shutdown scripts for easier deployment and management

## [0.4.6] - 2021-05-09
### Changed
- Updated apex-legends-api to version 2.0.3

## [0.4.5] - 2021-05-06
### Changed
- Updated apex-legends-api to version 2.0.2

## [0.4.4] - 2021-05-05
### Fixed
- Fixed bogus route in app.py
- Fixed issue with not reloading api events

## [0.4.3] - 2021-05-05
### Added
- Added a date picker to the home page

## [0.4.2] - 2021-05-04
- Added an 'online' indicator
- Updated to latest apex legends api to support S9

## [0.4.1] - 2021-05-03
### Added
- Added a small footer to the main page with the version number in it

## [0.4.0] - 2021-05-04
### Added
- Added a leaderboard to the landing page

## [0.3.8] - 2021-05-03
### Fixed
- Fixed script to output errors to log file

## [0.3.7] - 2021-05-03
### Fixed
- Fixed the logging so that it all goes to a mongo DB (makes it a lot easier to watch logs)

## [0.3.6] - 2021-05-03
### Changed
- fixed the script for loading the Apex DB to run on the server on deployment

## [0.3.5] - 2021-05-02
### Changed
- Changed the long-running script to make it run more efficiently
    - Added threads
    - Pull data only if needed
    - slow the loop if nobody is online

## [0.3.4]
### Added
- Add script for adding a new player to the DB by name

## [0.3.3] - 2021-04-30
### Changed
- Cleaned up the home page, so it doesn't look absolutely horrible

## [0.3.2] - 2021-04-30
### Fixed
- EMERGENCY FIX (part 2): lower case the legend names for the icon files (all of them)

## [0.3.1] - 2021-04-30
### Fixed
- EMERGENCY FIX: lower case the legend names for the icon files

## [0.3.0] - 2021-04-30
### Added
- Finished [Project to implement game day legend badges](https://github.com/johnsturgeon/apex-legends-tracker/projects/3)
- Add summary data next to thumbnail (Issue #38) 
- Add a small list of thumbnails for each legend played across the top (Issue #39)
- Added a small progress bar indicating percent of the stat for that day
### Fixed
- Small tweak to the deployment script to change where the maintenance file goes

## [0.2.1] - 2021-04-29
### Fixed
- Fixed an error in the deployment script for putting the site into maintenance mode

## [0.2.0] - 2021-04-29
### Fixed
- Fixed a bug with the data shown in the 'selected legend' banner

## [0.1.0] - 2021-04-27
### Added
- All basic functionality (documented in the [README.md](README.md))

### Changed
- Initial checkin

### Removed
- n/a
