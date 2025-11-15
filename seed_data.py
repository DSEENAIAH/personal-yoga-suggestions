from models import db, Asana, Sequence
import json
import os

def load_asana_data():
    """Load asana data from JSON files"""
    asana_files = [
        'mountain_pose.json', 'forward_fold.json', 'downward_dog.json', 
        'childs_pose.json', 'warrior_one.json', 'tree_pose.json',
        'cat_cow.json', 'cobra_pose.json', 'seated_meditation.json',
        'bridge_pose.json', 'legs_up_wall.json'
    ]
    
    asanas = []
    for filename in asana_files:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                asana = Asana(
                    name=data['name'],
                    sanskrit_name=data['sanskrit_name'],
                    overview_image=data['overview_image'],
                    step_data=json.dumps(data['steps']),
                    difficulty=data['difficulty'],
                    benefits=data['benefits']
                )
                asanas.append(asana)
    return asanas

def create_sequences():
    """Create sequences for the 6 emotions: anxious, stressed, sad, angry, overwhelmed, tired"""
    sequences = [
        # CALMING & GROUNDING SEQUENCES (for high-stress emotions)
        {
            'name': 'Anxiety Relief Flow',
            'emotion': 'anxious',
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 90},   # Mountain Pose (grounding)
                {'asana_id': 4, 'duration': 180},  # Child's Pose (safety)
                {'asana_id': 7, 'duration': 120},  # Cat-Cow (gentle movement)
                {'asana_id': 11, 'duration': 360}, # Legs Up Wall (nervous system reset)
                {'asana_id': 9, 'duration': 300}   # Seated Meditation (mindfulness)
            ]),
            'total_duration': 1050
        },
        {
            'name': 'Stress Release Flow', 
            'emotion': 'stressed',
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 60},   # Mountain Pose
                {'asana_id': 2, 'duration': 120},  # Forward Fold (surrender)
                {'asana_id': 7, 'duration': 150},  # Cat-Cow (spine release)
                {'asana_id': 4, 'duration': 180},  # Child's Pose (rest)
                {'asana_id': 11, 'duration': 240}, # Legs Up Wall (restoration)
                {'asana_id': 9, 'duration': 180}   # Seated Meditation
            ]),
            'total_duration': 930
        },
        {
            'name': 'Anger Cooling Flow',
            'emotion': 'angry', 
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 60},   # Mountain Pose (centering)
                {'asana_id': 2, 'duration': 150},  # Forward Fold (cooling)
                {'asana_id': 7, 'duration': 180},  # Cat-Cow (release tension)
                {'asana_id': 4, 'duration': 240},  # Child's Pose (surrender)
                {'asana_id': 11, 'duration': 300}, # Legs Up Wall (cool down)
                {'asana_id': 9, 'duration': 240}   # Seated Meditation (peace)
            ]),
            'total_duration': 1170
        },
        {
            'name': 'Overwhelm Relief Flow',
            'emotion': 'overwhelmed',
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 90},   # Mountain Pose (stability)
                {'asana_id': 4, 'duration': 300},  # Child's Pose (protection)
                {'asana_id': 7, 'duration': 120},  # Cat-Cow (gentle)
                {'asana_id': 11, 'duration': 420}, # Legs Up Wall (deep rest)
                {'asana_id': 9, 'duration': 360}   # Seated Meditation (clarity)
            ]),
            'total_duration': 1290
        },
        
        # ENERGIZING & UPLIFTING SEQUENCES (for low-energy emotions)
        {
            'name': 'Mood Lifting Flow',
            'emotion': 'sad',
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 60},   # Mountain Pose
                {'asana_id': 8, 'duration': 120},  # Cobra Pose (heart opening)
                {'asana_id': 10, 'duration': 150}, # Bridge Pose (lift mood)
                {'asana_id': 5, 'duration': 120},  # Warrior I (strength)
                {'asana_id': 6, 'duration': 90},   # Tree Pose (confidence)
                {'asana_id': 9, 'duration': 180}   # Seated Meditation
            ]),
            'total_duration': 720
        },
        {
            'name': 'Energy Boost Flow',
            'emotion': 'tired',
            'intensity_min': 1,
            'intensity_max': 5,
            'asana_sequence': json.dumps([
                {'asana_id': 1, 'duration': 45},   # Mountain Pose
                {'asana_id': 3, 'duration': 120},  # Downward Dog (energizing)
                {'asana_id': 8, 'duration': 90},   # Cobra Pose (awakening)
                {'asana_id': 5, 'duration': 120},  # Warrior I (power)
                {'asana_id': 10, 'duration': 90},  # Bridge Pose (vitality)
                {'asana_id': 6, 'duration': 75},   # Tree Pose (focus)
                {'asana_id': 9, 'duration': 120}   # Seated Meditation
            ]),
            'total_duration': 660
        }
    ]
    
    return [Sequence(**seq) for seq in sequences]

def seed_database():
    """Seed the database with asanas and sequences"""
    # Clear existing data
    db.drop_all()
    db.create_all()
    
    # Add asanas
    asanas = load_asana_data()
    for asana in asanas:
        db.session.add(asana)
    
    db.session.commit()
    
    # Add sequences
    sequences = create_sequences()
    for sequence in sequences:
        db.session.add(sequence)
    
    db.session.commit()
    print(f"Seeded {len(asanas)} asanas and {len(sequences)} sequences")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_database()