# Google setup: get your own client_secret.json

The helper talks to YouTube through Google's official API. Google requires every app to have
its own "OAuth client". This takes about 10 minutes, once, and is free. You need a Google
account (any account; it does not have to be the channel's account).

## 1. Create a project

1. Open https://console.cloud.google.com/projectcreate
2. Project name: `yt-autopilot`. Click **Create**.
3. Wait a few seconds, then make sure `yt-autopilot` is selected in the project picker at the
   top of the page.

## 2. Turn on the two YouTube APIs

1. Open https://console.cloud.google.com/apis/library
2. Search **YouTube Data API v3**, open it, click **Enable**.
3. Go back, search **YouTube Analytics API**, open it, click **Enable**.

## 3. Set up the consent screen

1. Open https://console.cloud.google.com/auth/overview and click **Get started**.
2. App name: `yt-autopilot`. User support email: your email. Click **Next**.
3. Audience: **External**. Click **Next**.
4. Contact email: your email. Click **Next**, tick the agreement, click **Create**.

## 4. Allow your channel's account to sign in

1. Open https://console.cloud.google.com/auth/audience
2. Under **Test users** click **Add users**.
3. Enter the Gmail address that owns the YouTube channel. Click **Save**.

Without this step Google shows "Access blocked" at sign-in.

## 5. Create the client and download the file

1. Open https://console.cloud.google.com/auth/clients and click **Create client**.
2. Application type: **Desktop app**. Name: `yt-autopilot-desktop`. Click **Create**.
3. Click **Download JSON**. The file is named like
   `client_secret_1234567890-abc.apps.googleusercontent.com.json`.
4. Rename it to exactly `client_secret.json` and put it in the same folder as `Install.bat`.

Now run `Install.bat` (or press Enter in the installer window if it is waiting).

## Good to know

- **Sign-in expires every 7 days** while the app is in "Testing" mode. To stop that, open
  https://console.cloud.google.com/auth/audience and click **Publish app**. Google then shows an
  "unverified app" warning at sign-in, which you click through once (Advanced, then Go to
  yt-autopilot). That is fine for personal use.
- **Keep client_secret.json private.** Do not commit it to Git or post it anywhere. It is
  already listed in `.gitignore`.
- The YouTube API allows about 6 uploads per day per project. Ask Claude "quota status" to see
  what is left.
