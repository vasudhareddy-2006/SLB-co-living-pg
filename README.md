# SLB Coliving PG

A concise, responsive website built with HTML, CSS and JavaScript. It keeps the existing warm look across the site, with a dedicated black, cherry-red, burgundy, ivory and silver Facilities section, one slow-scrolling amenity rail, a single SVG butterfly, PG photos, Google Maps directions and an enquiry form.

**Price note:** ₹18,000, ₹10,000, ₹8,000 and ₹7,000 are examples from another PG screenshot, not confirmed SLB Coliving PG rates. Confirm the real prices with the owner. The four-sharing card uses a clearly labelled concept image, not a photo of SLB.

## Run in VS Code

1. Download and unzip the project.
2. In VS Code, choose **File → Open Folder** and open the extracted folder.
3. Open `index.html`. With the **Live Server** extension, right-click the file and choose **Open with Live Server**.
4. Or run `python3 -m http.server 8000` in the VS Code terminal and visit <http://localhost:8000>.

## Main files

- `index.html`: page text, room cards, facilities, address, contacts and form.
- `style.css`: responsive design, room cards, the single Facilities marquee, one local butterfly and reduced-motion styles.
- `script.js`: mobile menu, photo viewer, form validation, amenity selection/details, and butterfly visibility behavior.
- `assets/images/`: photos supplied for the PG and the four-sharing concept image.

## Before publishing

Update prices in the four room cards in `index.html` only after the owner confirms them. The address and phone numbers shown are those supplied for the site: 1st Cross, AET College Road, Janatha Colony, Doddakannelli, Kadubeesanahalli, Bengaluru, Karnataka 560035, India; +91 99663 67235; +91 80741 55384.

The Facilities section contains only the supplied amenity list and no photographs. One slow, continuous right-to-left rail carries all 26 names in one sequence and loops seamlessly; its centered viewing window is sized to show at most one or two names at once. Selecting a name pauses the rail and opens its existing category note. One restrained red line-art butterfly travels within this section; page-wide decorative butterflies return elsewhere. Reduced-motion visitors see a static, wrapping amenities list. A food menu and resident reviews were not provided, so those sections are omitted. The form prepares a WhatsApp message for visitors to review and send; it does not save or send enquiries automatically.

For a simple public launch, upload the project folder to a static host such as Netlify. No build command is required. Test the map and phone links on a phone after publishing.
