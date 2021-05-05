# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Cleaned up the home page so it doesn't look absolutely horrible

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
