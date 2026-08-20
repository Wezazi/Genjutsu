I made this script because i wanted to get a better understanding of how javascript heavy sites like Instagram work. 

I was inspecting Instagram when i noticed that it was full of script elements rather than the rendered HTML, it was my first time seeing a site like that. Saving the page resulted in a extremely long file with weirdly nested elements which was difficult to work with. I wanted to find a way to only clone the login page so i could connect it to a php backend and turn it into a phishing site. I first manually cloned each element which was a very time consuming, it worked but was extremely inefficient so i wanted to automate it. My first script version was based on Accessibility.getFullAXTree but due to its limitations i had to rewrite the script entirely. This final script is based on DOMSnapshot.captureSnapshot instead. Tested on Instagram, google, and twitter

Expect to tweak the cloned site a bit and expect to modify the script a bit based on target site.  

I made this script a couple months ago and uploaded it to github but removed it a couple days after. I decided to re upload it today because i don't consider it powerful enough, I wouldn't even use this script myself if i were conducting a red team engagement. This script is pretty useless for purposes other than experimentation and education, there are much more effective and powerful phishing tools like evilginx.  

This script is made and purely meant for research and educational purposes.  

How to use:  

1.python -m venv venv  
2.venv\Scripts\activate  
3.pip install playwright  
4.playwright install  
5.python genjutsu.py  

Make sure to quickly press decline optional cookies while the script is running, otherwise the banner will appear in the cloned site
