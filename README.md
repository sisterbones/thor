<div align="center">
  <img height="128" src="./assets/logo.png" alt="Thor logo, decorative"/>
  <h1>THOR</h1>
  <p><strong>Lightning Detection & Alert System</strong></p>
</div>

# Install

## From source

The instructions assume you are using Linux. Windows support is likely but I have't tested it.

0. Install prerequisites

To install THOR like this, make sure you have:
- `python3`
- `python3-venv`
- `git`
- `sass` (for example with `sudo npm install -g sass`)

1. Clone the repository from GitHub

```bash
git clone https://github.com/sisterbones/thor.git
cd thor
git submodule init
```

2. Create a virtual environment and enter it

(Assumes you're using `bash`, may differ in different shells)

```bash
python -m venv .venv/
source .venv/bin/activate
```

Your shell should now look something like this:

```bash
(.venv) $
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

# 3rd Party Libraries

This repository includes the following third-party libraries:

- `socket.io-client`, [MIT License](https://github.com/socketio/socket.io/blob/7427109658591e7ce677a183a664d1f5327f37ea/LICENSE),
Copyright (c) 2014-present Guillermo Rauch and Socket.IO
contributors, [Source code](https://github.com/socketio/socket.io)

- Leaflet (CSS and
  JavaScript), [BSD 2-Clause "Simplified"](https://github.com/Leaflet/Leaflet/blob/142f94a9ba5757f7e7180ffa6cbed2b3a9bc73c9/LICENSE),
  Copyright (c) 2010-2024, Volodymyr Agafonkin, Copyright (c) 2010-2011,
  CloudMade, [Source code](https://github.com/Leaflet/Leaflet)

Additionally, it includes the following third-party libraries as Git submodules:

- Bootstrap
  v5.3, [MIT License](https://github.com/twbs/bootstrap/blob/0cbfe13adf669ad39ae9d8e873c2ad59befd3a3a/LICENSE),
  Copyright (c) 2011-2024 The Bootstrap Authors [Source code](https://github.com/twbs/bootstrap)
- Font Awesome 6
  Free, [CC-BY-4.0, Font Awesome Free License, Open Font License, Copyright (c) 2024 Fonticons, Inc.](https://github.com/FortAwesome/Font-Awesome/blob/c0f460dca7f7688761120415ff3c9cf7f73119be/LICENSE.txt), [Source code](https://github.com/FortAwesome/Font-Awesome)
