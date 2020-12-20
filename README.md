# Emote Collector Website

This is the code that powers https://ec.emote.bot.

## Installation

1. Make a new venv
2. pip install -r requirements.txt
3. Copy config.example.py to config.py and fill in your database information.
This should be the same database that Emote Collector Bot connects to.
4. Run start.sh
5. Edit [the Caddyfile](/Caddyfile) to your needs
6. Run caddy
7. *Optional step*: Set up onion services (beyond the scope of this README), and configure them in 
config.py

## License

<pre>
Emote Collector Website provides a list of emotes and an API for the Emote Collector bot.
Copyright © 2020 io mintz

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
</pre>
