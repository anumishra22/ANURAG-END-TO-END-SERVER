# Facebook Cookies Kaise Update Karein

## Problem
Messages fail ho rahe hain kyunki aapke Facebook cookies **expire** ho gaye hain.

## Solution: Fresh Cookies Kaise Le

### Step 1: Facebook Login Karein
1. Apne browser mein Facebook.com kholo aur login karein

### Step 2: Browser DevTools Kholo
- **Chrome/Edge**: Press `F12` ya right-click > Inspect
- **Firefox**: Press `F12`

### Step 3: Cookies Copy Karein

#### Method 1: Console se (Easiest)
1. DevTools mein **Console** tab par jao
2. Ye code paste karein aur Enter dabaye:
```javascript
document.cookie
```
3. Jo output aaye use **copy** kar lo

#### Method 2: Application/Storage Tab se
1. DevTools mein **Application** tab (Chrome) ya **Storage** tab (Firefox) par jao
2. Left side mein **Cookies** > **https://www.facebook.com** par click karein
3. Sabhi cookies copy karein is format mein:
```
cookie1=value1;cookie2=value2;cookie3=value3
```

### Step 4: cookies.txt Update Karein
1. Replit mein `cookies.txt` file kholo
2. Purane cookies **delete** karein
3. Naye cookies **paste** karein
4. File **save** karein

### Important Cookies (Required):
- `c_user` - Your Facebook user ID
- `xs` - Session token
- `datr` - Device token
- `fr` - Secure token

### Step 5: Server Restart Karein
Cookies update karne ke baad server automatically restart ho jayega aur messages send hone lagenge.

## Troubleshooting

### Agar phir bhi kaam na kare:
1. Facebook se **logout** karke phir **login** karein
2. Fresh cookies dobara le
3. Check karein ki sabhi required cookies hai

### Security Note
⚠️ Apne cookies **kabhi share mat karna** - ye aapka account access de sakte hain!
