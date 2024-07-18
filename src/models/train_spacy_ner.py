import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
import random
import logging
from tqdm import tqdm
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_annotated_data(data_dir):
    """Load annotated data from .spacy files"""
    nlp = spacy.blank("en")
    db = DocBin()
    file_paths = list(Path(data_dir).glob("*.spacy"))
    if not file_paths:
        logging.error(f"No .spacy files found in {data_dir}")
        sys.exit(1)
    for file_path in tqdm(file_paths, desc="Loading annotated data"):
        try:
            doc_bin = DocBin().from_disk(file_path)
            docs = list(doc_bin.get_docs(nlp.vocab))
            for doc in docs:
                db.add(doc)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
    if len(db) == 0:
        logging.error("No valid documents were loaded")
        sys.exit(1)
    logging.info(f"Loaded {len(db)} documents")
    return db

def create_examples(nlp, docs):
    """Create Example objects for training"""
    examples = []
    for doc in docs:
        example = Example.from_dict(nlp.make_doc(doc.text), {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]})
        examples.append(example)
    return examples

def evaluate_model(nlp, examples):
    """Evaluate the model's performance"""
    scorer = spacy.scorer.Scorer()
    examples = [Example(nlp(eg.text), eg.reference) for eg in examples]
    scores = scorer.score(examples)
    return scores

def train_spacy_model(train_data, val_data, output_dir, n_iter=100, dropout=0.2):
    """Train a custom spaCy NER model with early stopping"""
    nlp = spacy.blank("en")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Add labels
    for doc in train_data:
        for ent in doc.ents:
            ner.add_label(ent.label_)

    # Create training examples
    train_examples = create_examples(nlp, train_data)
    val_examples = create_examples(nlp, val_data)

    # Get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

    best_f_score = 0
    no_improvement = 0
    patience = 5  # Number of iterations to wait for improvement before early stopping

    with nlp.disable_pipes(*other_pipes):  # only train NER
        optimizer = nlp.initialize()
        for itn in range(n_iter):
            random.shuffle(train_examples)
            losses = {}
            batches = minibatch(train_examples, size=compounding(4.0, 32.0, 1.001))
            for batch in tqdm(batches, desc=f"Training - Iteration {itn + 1}/{n_iter}"):
                try:
                    nlp.update(batch, drop=dropout, losses=losses)
                except Exception as e:
                    logging.error(f"Error during training: {str(e)}")
                    logging.debug(f"Exception details: {repr(e)}")
                    continue
            
            # Evaluate on validation set
            try:
                scores = evaluate_model(nlp, val_examples)
                f_score = scores['ents_f']
                logging.info(f"Iteration {itn + 1} - Losses: {losses.get('ner', 0):.3f}, F-score: {f_score:.3f}")
                logging.debug(f"Full scores: {scores}")

                # Check for improvement
                if f_score > best_f_score:
                    best_f_score = f_score
                    no_improvement = 0
                    # Save the best model
                    nlp.to_disk(output_dir / "best_model")
                    logging.info(f"New best model saved with F-score: {best_f_score:.3f}")
                else:
                    no_improvement += 1
            
                # Early stopping
                if no_improvement >= patience:
                    logging.info(f"Stopping early after {itn + 1} iterations due to no improvement")
                    break
            except Exception as e:
                logging.error(f"Error during evaluation: {str(e)}")
                logging.debug(f"Exception details: {repr(e)}")
                continue

    logging.info(f"Final best F-score: {best_f_score:.3f}")

def main(data_dir, output_dir, n_iter=100):
    """Main function to load data, train model, and save it"""
    logging.info("Loading annotated data...")
    all_data = load_annotated_data(data_dir)
    
    # Split data into train and validation sets
    train_data, val_data = train_test_split(list(all_data.get_docs(spacy.blank("en").vocab)), test_size=0.2, random_state=42)
    
    logging.info(f"Training data: {len(train_data)} documents")
    logging.info(f"Validation data: {len(val_data)} documents")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Training spaCy NER model...")
    train_spacy_model(train_data, val_data, output_dir, n_iter)
    
    logging.info("Training complete!")

if __name__ == "__main__":
    import argparse
    from sklearn.model_selection import train_test_split
    
    parser = argparse.ArgumentParser(description="Train a custom spaCy NER model")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing annotated .spacy files")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save the trained model")
    parser.add_argument("--n_iter", type=int, default=100, help="Maximum number of training iterations")
    
    args = parser.parse_args()
    
    main(args.data_dir, args.output_dir, args.n_iter)