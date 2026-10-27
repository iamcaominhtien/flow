# Briefs: Screen flow

One brief at level C. Written for this repository (not by the research tool), from the screen flow design page. It is **not** read by `check_briefs.py` (the checker expects every type to have levels A, B and C); the generator that wrote it counted the elements and connections below. See [README](README.md) for how to run a brief.

---

## screen-C-01 — Ride-Hailing App: Booking, Trip, Payment, Account and Web Receipts

* **type:** screen
* **level:** C
* **elements:** 52
* **connections:** 77
* **groups:** Entry Points, Onboarding, Booking, Trip, Payments, Account, Web Portal

### Brief

The flow has 52 items in 7 groups: Entry Points, Onboarding, Booking, Trip, Payments, Account, Web Portal. Each name below is one screen to draw, except the three names ending in Check, which are decisions, and the three names in Entry Points, which are ways into the app. Every sentence is one connection to draw. The app screens are phone screens; the Web Portal screens are desktop browser screens. A tap or a click is something the person does, and a timer, an API answer or a push is something the system does.

In Entry Points: From AppIcon, launch the app goes to SplashScreen. From PushTripUpdate, tap the push notification goes to InTrip. From DeepLinkPromo, open the promo link goes to PromoCodeSheet.

In Onboarding: From SplashScreen, the timer ends after 2 s goes to HasSessionCheck. From HasSessionCheck, [session valid] goes to HomeMap. From HasSessionCheck, [no session] goes to WelcomeCarousel. From WelcomeCarousel, tap Get started goes to PhoneEntry. From PhoneEntry, tap Send code goes to OtpVerification. From OtpVerification, tap Wrong number goes to PhoneEntry. From OtpVerification, [code valid] goes to ProfileSetup. From ProfileSetup, tap Continue goes to LocationPermission. From LocationPermission, tap Allow goes to NotificationPermission. From LocationPermission, tap Not now goes to HomeMap. From NotificationPermission, tap Allow or Skip goes to HomeMap.

In Booking: From HomeMap, tap Where to goes to DestinationSearch. From DestinationSearch, tap Saved goes to SavedPlaces. From SavedPlaces, tap Back goes to DestinationSearch. From DestinationSearch, tap a result goes to RideOptions. From SavedPlaces, tap a place goes to RideOptions. From RideOptions, tap Choose ride goes to FareEstimate. From FareEstimate, tap Add promo goes to PromoCodeSheet. From PromoCodeSheet, tap Apply goes to FareEstimate. From FareEstimate, tap Confirm goes to ConfirmPickup. From ConfirmPickup, tap Request ride goes to FindingDriver. From FindingDriver, the API answers goes to DriverFoundCheck. From DriverFoundCheck, [driver accepted] goes to DriverAssigned. From DriverFoundCheck, [no driver after 60 s] goes to NoDriversFound. From NoDriversFound, tap Try again goes to FindingDriver. From NoDriversFound, tap Change ride goes to RideOptions. From FindingDriver, tap Cancel goes to HomeMap. From DriverAssigned, the screen advances on its own goes to DriverArriving. From HomeMap, tap Profile tab goes to ProfileTab.

In Trip: From DriverArriving, tap Message goes to ChatWithDriver. From ChatWithDriver, tap Back goes to DriverArriving. From DriverArriving, the driver starts the trip goes to InTrip. From DriverArriving, tap Cancel ride goes to HomeMap. From InTrip, tap Share goes to ShareTripStatus. From ShareTripStatus, tap Done goes to InTrip. From InTrip, tap SOS goes to SosEmergency. From SosEmergency, tap I am safe goes to InTrip. From SosEmergency, tap Call support goes to SupportHelp. From InTrip, the car reaches the drop-off goes to TripComplete. From TripComplete, tap Rate goes to RateDriver. From RateDriver, tap Submit goes to TipDriver.

In Payments: From TipDriver, tap Pay goes to PaymentApprovedCheck. From PaymentApprovedCheck, [card approved] goes to ReceiptView. From PaymentApprovedCheck, [card declined] goes to PaymentFailed. From PaymentFailed, tap Change method goes to PaymentMethods. From PaymentFailed, tap Retry goes to TipDriver. From PaymentMethods, tap Add card goes to AddCard. From AddCard, tap Save goes to ThreeDSecure. From ThreeDSecure, the bank answers goes to PaymentApprovedCheck. From PaymentMethods, tap Top up goes to WalletTopUp. From WalletTopUp, tap Done goes to PaymentMethods. From ReceiptView, tap Done goes to TripHistory. From TripHistory, tap Home tab goes to HomeMap.

In Account: From ProfileTab, tap Settings goes to SettingsScreen. From ProfileTab, tap Safety goes to SafetyCenter. From SafetyCenter, tap Contacts goes to TrustedContacts. From TrustedContacts, tap Back goes to SafetyCenter. From ProfileTab, tap Help goes to SupportHelp. From ProfileTab, tap Your trips goes to TripHistory. From SettingsScreen, tap Payment goes to PaymentMethods. From SettingsScreen, tap Delete account goes to DeleteAccountConfirm. From DeleteAccountConfirm, tap Confirm goes to SplashScreen. From DeleteAccountConfirm, tap Cancel goes to SettingsScreen. From SettingsScreen, tap Sign out goes to SignOutConfirm. From SignOutConfirm, tap Confirm goes to WelcomeCarousel.

In Web Portal: From WebLogin, click Sign in [credentials valid] goes to WebTripList. From WebTripList, click a trip goes to WebTripDetail. From WebTripDetail, click Receipt goes to WebReceiptPdf. From WebReceiptPdf, click Close goes to WebTripDetail. From WebTripDetail, click Request invoice goes to WebInvoiceRequest. From WebInvoiceRequest, click Back goes to WebTripDetail. From WebTripList, click Profile goes to WebProfile. From WebProfile, click Sign out goes to WebLogout. From WebLogout, the page reloads goes to WebLogin.

### Must show

* The 7 groups (Entry Points, Onboarding, Booking, Trip, Payments, Account, Web Portal) hold exactly the items listed under Structure, and the Web Portal is its own zone below the phone flow.
* Phone screens are drawn in phone frames and Web Portal screens in desktop browser frames; the three Check items are diamonds.
* The three entry points are separate pills on the left, and each one runs into the screen it opens.
* A person's action and the system's action look different: taps and clicks one way, the 2 s timer, the API answers and the push another way.
* Fan-out of three or more: ProfileTab (4).
* 22 connections return to an earlier item: SavedPlaces to DestinationSearch, PromoCodeSheet to FareEstimate, ChatWithDriver to DriverArriving, ShareTripStatus to InTrip, SosEmergency to InTrip, TripHistory to HomeMap, ThreeDSecure to PaymentApprovedCheck, WalletTopUp to PaymentMethods, PaymentFailed to TipDriver, DriverArriving to HomeMap, NoDriversFound to FindingDriver, NoDriversFound to RideOptions, FindingDriver to HomeMap, DeleteAccountConfirm to SplashScreen, DeleteAccountConfirm to SettingsScreen, OtpVerification to PhoneEntry, NotificationPermission to HomeMap, LocationPermission to HomeMap, TrustedContacts to SafetyCenter, WebReceiptPdf to WebTripDetail, WebInvoiceRequest to WebTripDetail, WebLogout to WebLogin.
* 16 connections cross between groups, for example AppIcon to SplashScreen, NotificationPermission to HomeMap, SettingsScreen to PaymentMethods.

### Traps

* Six screens hand control to one hub (HomeMap) from four different groups, and PaymentApprovedCheck is entered from two directions (a tap and a bank answer), so a forward layout runs into returns.
* Three overlays-like detours (PromoCodeSheet, SosEmergency, DeleteAccountConfirm) return to the screen they came from; a retry loop (NoDriversFound to FindingDriver) is nested in the forward path.
* A tab bar (HomeMap, ProfileTab, TripHistory) links screens in three groups.

### Structure

**Elements**

- Entry Points: AppIcon, PushTripUpdate, DeepLinkPromo
- Onboarding: SplashScreen, HasSessionCheck, WelcomeCarousel, PhoneEntry, OtpVerification, ProfileSetup, LocationPermission, NotificationPermission
- Booking: HomeMap, DestinationSearch, SavedPlaces, RideOptions, FareEstimate, PromoCodeSheet, ConfirmPickup, FindingDriver, DriverFoundCheck, NoDriversFound, DriverAssigned
- Trip: DriverArriving, ChatWithDriver, InTrip, ShareTripStatus, SosEmergency, TripComplete, RateDriver
- Payments: TipDriver, PaymentApprovedCheck, ReceiptView, PaymentFailed, PaymentMethods, AddCard, ThreeDSecure, WalletTopUp, TripHistory
- Account: ProfileTab, SettingsScreen, SafetyCenter, TrustedContacts, SupportHelp, DeleteAccountConfirm, SignOutConfirm
- Web Portal: WebLogin, WebTripList, WebTripDetail, WebReceiptPdf, WebInvoiceRequest, WebProfile, WebLogout

**Connections**

- AppIcon -> SplashScreen (launch the app)
- PushTripUpdate -> InTrip (tap the push notification)
- DeepLinkPromo -> PromoCodeSheet (open the promo link)
- SplashScreen -> HasSessionCheck (the timer ends after 2 s)
- HasSessionCheck -> HomeMap ([session valid])
- HasSessionCheck -> WelcomeCarousel ([no session])
- WelcomeCarousel -> PhoneEntry (tap Get started)
- PhoneEntry -> OtpVerification (tap Send code)
- OtpVerification -> PhoneEntry (tap Wrong number)
- OtpVerification -> ProfileSetup ([code valid])
- ProfileSetup -> LocationPermission (tap Continue)
- LocationPermission -> NotificationPermission (tap Allow)
- LocationPermission -> HomeMap (tap Not now)
- NotificationPermission -> HomeMap (tap Allow or Skip)
- HomeMap -> DestinationSearch (tap Where to)
- DestinationSearch -> SavedPlaces (tap Saved)
- SavedPlaces -> DestinationSearch (tap Back)
- DestinationSearch -> RideOptions (tap a result)
- SavedPlaces -> RideOptions (tap a place)
- RideOptions -> FareEstimate (tap Choose ride)
- FareEstimate -> PromoCodeSheet (tap Add promo)
- PromoCodeSheet -> FareEstimate (tap Apply)
- FareEstimate -> ConfirmPickup (tap Confirm)
- ConfirmPickup -> FindingDriver (tap Request ride)
- FindingDriver -> DriverFoundCheck (the API answers)
- DriverFoundCheck -> DriverAssigned ([driver accepted])
- DriverFoundCheck -> NoDriversFound ([no driver after 60 s])
- NoDriversFound -> FindingDriver (tap Try again)
- NoDriversFound -> RideOptions (tap Change ride)
- FindingDriver -> HomeMap (tap Cancel)
- DriverAssigned -> DriverArriving (the screen advances on its own)
- DriverArriving -> ChatWithDriver (tap Message)
- ChatWithDriver -> DriverArriving (tap Back)
- DriverArriving -> InTrip (the driver starts the trip)
- DriverArriving -> HomeMap (tap Cancel ride)
- InTrip -> ShareTripStatus (tap Share)
- ShareTripStatus -> InTrip (tap Done)
- InTrip -> SosEmergency (tap SOS)
- SosEmergency -> InTrip (tap I am safe)
- SosEmergency -> SupportHelp (tap Call support)
- InTrip -> TripComplete (the car reaches the drop-off)
- TripComplete -> RateDriver (tap Rate)
- RateDriver -> TipDriver (tap Submit)
- TipDriver -> PaymentApprovedCheck (tap Pay)
- PaymentApprovedCheck -> ReceiptView ([card approved])
- PaymentApprovedCheck -> PaymentFailed ([card declined])
- PaymentFailed -> PaymentMethods (tap Change method)
- PaymentFailed -> TipDriver (tap Retry)
- PaymentMethods -> AddCard (tap Add card)
- AddCard -> ThreeDSecure (tap Save)
- ThreeDSecure -> PaymentApprovedCheck (the bank answers)
- PaymentMethods -> WalletTopUp (tap Top up)
- WalletTopUp -> PaymentMethods (tap Done)
- ReceiptView -> TripHistory (tap Done)
- TripHistory -> HomeMap (tap Home tab)
- HomeMap -> ProfileTab (tap Profile tab)
- ProfileTab -> SettingsScreen (tap Settings)
- ProfileTab -> SafetyCenter (tap Safety)
- SafetyCenter -> TrustedContacts (tap Contacts)
- TrustedContacts -> SafetyCenter (tap Back)
- ProfileTab -> SupportHelp (tap Help)
- ProfileTab -> TripHistory (tap Your trips)
- SettingsScreen -> PaymentMethods (tap Payment)
- SettingsScreen -> DeleteAccountConfirm (tap Delete account)
- DeleteAccountConfirm -> SplashScreen (tap Confirm)
- DeleteAccountConfirm -> SettingsScreen (tap Cancel)
- SettingsScreen -> SignOutConfirm (tap Sign out)
- SignOutConfirm -> WelcomeCarousel (tap Confirm)
- WebLogin -> WebTripList (click Sign in [credentials valid])
- WebTripList -> WebTripDetail (click a trip)
- WebTripDetail -> WebReceiptPdf (click Receipt)
- WebReceiptPdf -> WebTripDetail (click Close)
- WebTripDetail -> WebInvoiceRequest (click Request invoice)
- WebInvoiceRequest -> WebTripDetail (click Back)
- WebTripList -> WebProfile (click Profile)
- WebProfile -> WebLogout (click Sign out)
- WebLogout -> WebLogin (the page reloads)

### Sources

* Flow design page `docs/design/02-screen-flow.md` (ids, device frames, triggers, guards, zones, entry points, tab bus, overlays).

### Uncertain

* The product details are invented to give the flow a realistic shape; they are not taken from a real app.
