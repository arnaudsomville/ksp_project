import krpc
import time

import krpc.client

# Se connecter au serveur kRPC
def connect_to_server():
    """
    Établit une connexion avec le serveur kRPC dans Kerbal Space Program.
    """
    print("Connexion au serveur kRPC...")
    conn = krpc.connect(name='KSP Automated Maneuver')
    print(f"Connecté au serveur kRPC, version {conn.krpc.get_status().version}")
    return conn

# Planifier une manœuvre
def plan_maneuver(conn, vessel, delta_v, burn_time_from_now):
    """
    Planifie une manœuvre à exécuter dans un futur proche.

    Args:
        conn: La connexion kRPC.
        vessel: Le vaisseau actif.
        delta_v: Un tuple contenant le delta-v en m/s (prograde, normal, radial).
        burn_time_from_now: Temps en secondes avant de commencer la manœuvre.

    Returns:
        node: Le nœud de manœuvre créé.
    """
    print("Planification de la manœuvre...")
    ut = conn.space_center.ut  # Temps universel
    node = vessel.control.add_node(
        ut + burn_time_from_now,  # Temps auquel effectuer la manœuvre
        prograde=delta_v[0],      # Composante prograde
        normal=delta_v[1],        # Composante normale
        radial=delta_v[2]         # Composante radiale
    )
    print(f"Manœuvre planifiée dans {burn_time_from_now} secondes avec ΔV={delta_v}.")
    return node

# Exécuter la manœuvre
def execute_maneuver(conn: krpc.Client, vessel: krpc.Client, node):
    """
    Exécute une manœuvre planifiée.

    Args:
        conn: La connexion kRPC.
        vessel: Le vaisseau actif.
        node: Le nœud de manœuvre à exécuter.
    """
    print("Alignement sur le nœud de manœuvre...")
    vessel.auto_pilot.reference_frame = node.reference_frame
    vessel.auto_pilot.target_direction = (0, 1, 0)
    vessel.auto_pilot.engage()
    vessel.auto_pilot.wait()

    # Vérifier si les moteurs sont prêts
    if vessel.available_thrust <= 0:
        print("Aucun moteur actif ou disponible. Activation du prochain étage...")
        vessel.control.activate_next_stage()

        # Réessayer après activation de l'étage
        time.sleep(1)  # Attendre que les moteurs s'activent
        if vessel.available_thrust <= 0:
            raise RuntimeError("Pas de poussée disponible après activation de l'étage.")

    print("Attente du moment de la poussée...")
    burn_time = node.remaining_delta_v / vessel.available_thrust  # Temps estimé pour la poussée
    burn_start = conn.space_center.ut + node.time_to - (burn_time / 2)  # Correction ici

    while conn.space_center.ut < burn_start:  # Correction ici
        time.sleep(0.1)

    print("Début de la poussée...")
    vessel.control.throttle = 1.0
    while node.remaining_delta_v > 0.1:  # Tolérance pour stopper la poussée
        time.sleep(0.1)

    vessel.control.throttle = 0.0
    print("Manœuvre terminée. Suppression du nœud.")
    node.remove()

# Fonction principale
def main():
    """
    Fonction principale pour automatiser une manœuvre.
    """
    # Connexion au serveur
    conn = connect_to_server()
    vessel = conn.space_center.active_vessel

    # Planifier une manœuvre : exemple avec un ΔV de 100 m/s prograde dans 60 secondes
    delta_v = (100, 0, 0)  # Prograde, Normal, Radial
    burn_time_from_now = 60  # Temps avant la manœuvre en secondes
    node = plan_maneuver(conn, vessel, delta_v, burn_time_from_now)

    # Exécuter la manœuvre
    execute_maneuver(conn, vessel, node)

    print("Mission accomplie.")

if __name__ == "__main__":
    main()