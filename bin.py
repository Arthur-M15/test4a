import threading
import time

# Verrou global pour synchroniser l'accès à la fonction
lock = threading.Lock()


# Fonction qui simule un travail long
def long_task():
    with lock:  # S'assure qu'une seule exécution de cette fonction se fait à la fois
        print("Démarrage de la tâche longue...")
        time.sleep(2)  # Simule un délai de traitement
        print("Tâche longue terminée.")


# Boucle principale
def main_loop():
    while True:
        # Vérifie si la fonction est déjà en cours d'exécution
        if lock.locked():  # Si le verrou est activé, cela signifie que la fonction est en cours
            print("La fonction est en cours d'exécution. Attente avant de réessayer...")
        else:
            # Lancer la fonction dans un thread séparé
            thread = threading.Thread(target=long_task)
            thread.start()

        time.sleep(0.5)  # Simule la boucle principale qui ne fait que tourner, sans attendre la fonction longue


if __name__ == "__main__":
    main_loop()
