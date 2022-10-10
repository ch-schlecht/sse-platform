Client Roles in Userinfo request mit schicken lassen (im realm):
- Roles anlegen und zuweisen:
  - (client anlegen)
  - (roles im client anlegen)
  - (users -> role mappings -> client roles -> user zu roles hinzufügen)
- client scopes -> profile -> mappers --> add builtin --> client roles adden
- client roles -> add to userinfo auf on


Admin Account der User anschauen darf (im realm):
- account anlegen (oder existierenden nehmen)
- users -> (der user) -> role Mappings -> client roles -> realm-management
- view-users role assignen
- KeycloakAdmin Python-Klasse kann dann mit diesen Credentials User und Gruppen abgefragen


oder ohne user (etwas umständlicher, lange nicht mehr getestet):
- über admin cli in master realm
- clients -> (realm-name)-realm (bei uns als SOSERVE-realm)
  - access type auf confidential umstellen, client id und secret generieren
  - service accounts enabled ON
  - service account roles --> client roles --> (REALM)-realm, view-users assignen
  - dann diese client id und secret in KeycloakAdmin reingeben (realm leer oder master)
  - ist so kompliziert, weil sobald man client_secret_key bei KeycloakAdmin setzt, der realm automatisch zu master gessetzt wird (warum auch immer)