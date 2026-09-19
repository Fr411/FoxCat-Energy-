# FoxCat Energy 1.4.3 — PRI hybride maison/réseau

## Nouveau moteur PRI
- Base issue de l'ancienne carte PRI jugée plus stable.
- Cible maison par paliers de 400 W / 10 %.
- Utilisation de `ceil()` : FoxCat ne crée pas volontairement un import par arrondi inférieur.
- Le réseau réel reste l'arbitre final.
- Import > zone morte : remontée PRI de 10 %.
- Export > zone morte : descente PRI de 10 % uniquement si la marche projetée ne crée pas un import excessif.
- Zone morte : maintien afin d'éviter les oscillations.
- Comparateur PV/plafond PRI conservé pour distinguer soleil limitant et PV réellement bridé.
- Le mode dynamique conserve sa couche tarifaire mais réutilise la même boucle physique.

## Cas de référence validé
PV ≈ 1,22 kW, import ≈ 1,04 kW, maison ≈ 2,26 kW, PRI 90 % :
FoxCat ordonne 100 %, et surtout ne descend plus vers la cible maison pendant un import réseau.

## Protections conservées
- synchronisation sur trames énergétiques ;
- une seule marche de 10 % maximum par trame ;
- ACK RRCR ;
- validation sur vraie trame N+1 ;
- comparateur PRI/PV ;
- gestion reset Smappee et stabilisation ;
- cycles machines protégés ;
- priorité utilisateur ;
- délestage haute consommation ;
- boiler et comptabilité énergétique ;
- Coûts & Bilan 1.4.2.
