# Campaign Hosting

Campaign hosting will let a DM start a campaign session, share a short join code,
and allow remote players to connect over the internet.

## Target Flow

1. The DM opens a campaign and selects **Host Campaign**.
2. The app creates a hosted campaign session with a short join code.
3. Players choose **Join Campaign**, enter the code, and claim or upload a
   character.
4. The DM sees connected players, character assignments, and readiness state.
5. Combat actions, targeting, resources, concentration, inventory changes, and
   log entries synchronize through the hosted session.

## Architecture

The first implementation stores hosting state as JSON-backed domain data:

- hosted session id
- campaign id
- join code
- host player id
- connected players
- player roles
- optional relay URL
- lifecycle status

The internet transport should plug into this model instead of replacing it. A
future relay server can exchange signed session messages while the desktop app
continues to use the same controller and rules engine path.

## Delivery Slices

1. Hosted session model, join code lifecycle, and persistence.
2. GUI commands for **Host Campaign** and **Join Campaign**.
3. Local loopback multiplayer smoke test. Completed: independent host and guest
   app instances discover a session, join by code, activate, disconnect, and
   close through the same isolated JSON store.
4. WebSocket relay protocol for campaign state messages.
5. DM lobby with connected players, ready checks, and character assignment.
6. Action synchronization through the unified combat action resolver.

The completed loopback test validates the backend contract and persistence
boundary. It does not open a network listener; the WebSocket relay slice is the
first Internet transport implementation.
7. Conflict handling, reconnect, and session recovery.
8. Public beta relay deployment and connection diagnostics.
