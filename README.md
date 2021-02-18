# modox
Modox is a Python package that consists of a collection of modules with utility classes and functions that enhance Python API in MODO.
I've been writing this package as part of my Auto Character System development effort and thought it might be useful resource for MODO community.

#### MODOX IS NOT DEVELOPED AS GENERAL PURPOSE LIBRARY. I AM PUBLISHING IT FOR EDUCATIONAL PURPOSES ONLY.



### IMPORTANT NOTES

  * You can copy/paste classes and functions published in this repository to your own projects.

  * I DO NOT RECOMMEND using this library directly within your MODO kit. I am using modox as-is within ACS3. If you use modox as-is in your own project and want to use ACS3 - you will get a conflict.

  * I DO NOT SUPPORT this library.

  * I DO NOT GUARANTEE backwards compatibility with any subsequent updates to this codebase. As mentioned above, I develop modox as part of ACS3 so I update/refactor/change it in any way I see fit for further ACS3 development.



### ABOUT CODEBASE

  * ACS3 is mainly dealing with the items, modifiers, channels and relationships between them so the natural focus of modox is in this area. You won't find any functionality focused on modeling or shading here.
  
  * Most of the codebase is in the form of class methods grouped into classes. This makes it rather easy to copy functions to different codebase and having it work without making any adjustments. The `Item` class is different, it extends MODO's native `modo.Item` class. In the beginning that was the idea, to extend native `modo` library. However, in the course of development it appeared that using separate class methods works better for my purposes.
  
  * I put a fair amount of effort into documenting the code, there should be comments for most of the functions contained in the library. 

  * There are some inconsistencies, unfinished functions and probably minor mistakes. If you find anything that's worth fixing/improving - let me know.



Considering all of the above, I hope you'll find this resource useful.
