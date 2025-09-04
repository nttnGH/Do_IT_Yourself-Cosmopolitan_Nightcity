# Cosmopolitan Night City - DIY Edition

DIY-CNC is a software tool that lets you create a fully personalized multilingual experience, just like the ["Cosmopolitan Night City"](https://www.nexusmods.com/cyberpunk2077/mods/5909) mod and ["Polyglot V"] mod (https://www.nexusmods.com/cyberpunk2077/mods/9275), but it's fully customizable. Select which characters switch languages, and with whom V is polyglot (with an AI or VA voice), enjoy all the advanced features (kiroshi translation effect, correct vomap, correct dialogue duration), specify exactly which audio and subtitle languages you need, and benefit from full integration with extension ["Change V's native Language"](https://www.nexusmods.com/cyberpunk2077/mods/5718).


## 🛠️ About the Code

DIY-CNC is a Python-based graphical tool with an easy-to-use interface built with **Tkinter**.

The tool provides full control over localization customization, allowing users to:
- Select which audio localization to modify,
- Select which subtitle language to modify,
- Choose which characters switch languages individually,
- Choose with whom V switch language.

It also automates complex file manipulations such as:
- Processing and merging **voiceover** files from different localizations of the game into a new customized set,
- Handling **lipsync** animations and generating **lipmaps** based on the combined voiceover files,
- Updating **voiceover maps** to prevent **misgendered issues** caused by file replacements,
- Updating **dialogue durations** to prevent **speech-cutting issues** after merging different localizations,
- Editing **subtitle files** to match custom configurations and applying a **Kiroshi translation effect** on the newly added lines,
- Cleaning up intermediate files to prepare the project for final mod packaging with external tools like **WolvenKit**.


## 📥 Downloads and Usage

You can view and explore the source code here:
- 👉 [View the source code on GitHub.](https://github.com/nttnGH/Do_IT_Yourself-Cosmopolitan_Nightcity)
The Github repository only contains the **source code** of DIY-CNC. Please note that the source code **cannot function on its own**, as it requires external files.

To use the tool, please download the full executable package (including the required files) here:
- 👉 [Download DIY-CNC executable on NexusMods.](https://www.nexusmods.com/cyberpunk2077/mods/20715)
A complete tutorial explaining how to use DIY-CNC and how to package the final result with WolvenKit is available on the NexusMods mod page.


## 📄 License

- The **DIY-CNC source code** was created by me, and is licensed under the [MIT License](https://opensource.org/licenses/MIT).  

- The **localization files** from *Cyberpunk 2077* included in the 7zip archive and processed by this tool are the exclusive property of **CD Projekt Red**.  
  These files are provided strictly for **modding purposes**, in accordance with CD Projekt Red's modding guidelines. I do not claim ownership of these assets.
  These files are **NOT included** on Github, but they are available on NexusMods.


## ✋ Author's Intent

While the DIY-CNC tool is free to use and modify under the MIT License,  
**I kindly ask that you do not upload** your own versions of *Cosmopolitan Night City / Polyglot V* created with DIY-CNC on NexusMods or any other platform.

There are already two official plug-and-play editions available:
- **Cosmopolitan Night City - Enhanced edition**
- **Cosmopolitan Night City - Lite edition**

As well as multiple Polyglot V mods.

I would like to keep the focus and visibility on these **official editions**.  
Please enjoy creating your own version for **personal use only**.

🙏 Thank you for your understanding and for supporting *Cosmopolitan Night City*!






📝 Changelog
v1

Initial release.


v1.5

Fixed subtitle display issues related to the "Rich color" tag.

Fixed encoding issues with quotation marks in subtitles.

Fixed a bug that caused WolvenKit to fail detecting some DIY-CNC project folders for certain users.


v1.6

Fixed various localization bugs in multiple languages. 

Adapted the base files for version 2.3 of the game.





v2.0

Polyglot V is now integrated by default into DIY-CNC, allowing you, with certain characters, to choose whether V speaks a different language, and whether V use VA or AIUS voices.

Polyglot V can now speak Spanish and Japanese and Korean and Chinese and Brazilian and French in addition to their native language.

Reorganization of NPC selection to allow proper use with Polyglot V.

Added a "Previous" button during NPC selection.



v2.1

Change V's native Language is now integrated by default into DIY-CNC; require to download one extension of your choice.

Fix CVL - PV incompatibility bug.










