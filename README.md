# Nexus Discord Bot

Nexus is a versatile Discord bot designed to enhance the interaction and entertainment in your Discord servers. It features a variety of commands and functionalities, including the unique ability to join voice channels and play sounds.

## Features

- **Voice Trolling**: Randomly joins a voice channel with members and plays a sound from a predefined list.
- **Music Commands**: Allows user to play music from youtube using a query/url.

## Installation

To install and run Nexus on your system, follow these steps:

1. **Clone the Repository**
   ```sh
   git clone https://github.com/ProtonDev-sys/Nexus.git
   cd Nexus
   ```

2. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**
   - Nexus requires FFmpeg for voice functionalities.
   - Download and install FFmpeg from [FFmpeg's official website](https://ffmpeg.org/download.html).
   - Ensure FFmpeg is added to your system's PATH.

4. **Configuration**
   - Create a `.env` file in the root directory.
   - Add your Discord bot token:
     ```
     DISCORD_TOKEN=your_bot_token_here
     ```

5. **Running the Bot**
   ```sh
   start.bat
   ```

## Usage

After inviting Nexus to your Discord server, you can interact with it using various commands.
### Music Commands
- /Play
- /Pause
- /Skip
- /Seek
- /Stop
- /Queue
### Level commands
- /Rank

## Contributing

Contributions to Nexus are welcome! If you have suggestions or improvements, feel free to fork the repository and submit a pull request.

## Acknowledgements

- Thanks to all contributors and users of Nexus!

```
