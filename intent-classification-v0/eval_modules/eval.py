"""Eval.

Using the eval.csv file, evaluate the performance of the classifier for each intent.

TODO: curently only works with single intent lables on the golden set, need to add support for multi intent labels on golden.

"""

import pandas as pd

from ml_modules.rule_based_clustering import RuleBasedClassifier, preprocess_tweet


class ClassificationEval(object):
    def __init__(self, eval_frame, classifier_instance):
        self.classifier = classifier_instance
        self.eval_frame = eval_frame

    def __eval_fn(self, arg):
        def err():
            print(f"No funciton named 'classify()' found in {self.classifier}")
        func = getattr(self.classifier, 'classify', err)
        # TODO find a more robust way of getting at most one item and/or handling multiclass eval.
        return func(arg)

    def __all_intents_fn(self):
        def err():
            print(
                f"No funciton named 'all_intents()' found in {self.classifier}")
        func = getattr(self.classifier, 'all_intents', err)
        return func()

    def __prep_eval_frame(self, df):
        # Fill NaNs with empty strings to include no intent tweets.
        df = df.fillna("")
        df = df[df['label'].notna()]
        df = df[df['tweet_text'].notna()]
        df['tweet_text'] = df['tweet_text'].apply(preprocess_tweet)
        # Only needed columps
        df = df[['tweet_text', 'label']]
        # One hot encode the labels.
        for intent in self.__all_intents_fn():
            df[f'{intent}_golden'] = df['label'] == intent
        return df

    def __prep_classification_frame(self, df):
        """Only using tweet_text, return a one hot encoded prediciton frame"""
        all_intents = self.__all_intents_fn()
        # Returns a set.
        df['predicted'] = df['tweet_text'].apply(self.__eval_fn)

        # Create a one hot encoded frame.
        for intent in all_intents:
            df[f'{intent}_pred'] = df['predicted'].apply(lambda x: intent in x)

        del df['predicted']
        return df

    def eval(self):
        df = self.__prep_eval_frame(self.eval_frame)
        df = self.__prep_classification_frame(df)

        df['predicted'] = df['tweet_text'].apply(self.__eval_fn)
        for intent in self.__all_intents_fn():
            # Calculate false positives.
            df[f'{intent}_fp'] = df.apply(
                lambda x: not x[f'{intent}_golden'] and x[f'{intent}_pred'], axis=1)
            # Calculate false negatives.
            df[f'{intent}_fn'] = df.apply(
                lambda x: x[f'{intent}_golden'] and not x[f'{intent}_pred'], axis=1)
            # Calculate true positives.
            df[f'{intent}_tp'] = df.apply(
                lambda x: x[f'{intent}_golden'] and x[f'{intent}_pred'], axis=1)

        # Calcualte metrics for each intent.
        for intent in self.__all_intents_fn():
            print(f"Intent: {intent}")
            print("==================================")
            # Calculate precision.
            precision = df[f'{intent}_tp'].sum(
            ) / (df[f'{intent}_tp'].sum() + df[f'{intent}_fp'].sum())
            print(f"{intent} Precision: {precision:.2f}")
            # Calculate recall.
            recall = df[f'{intent}_tp'].sum(
            ) / (df[f'{intent}_tp'].sum() + df[f'{intent}_fn'].sum())
            print(f"{intent} Recall: {recall:.2f}")
            # Calculate F1 score.
            f1 = 2 * (precision * recall) / (precision + recall)
            print(f"{intent} F1: {f1:.2f}")
            print("")

        return df


if __name__ == '__main__':
    eval_frame = pd.read_csv("eval.csv")[:100]
    eval = ClassificationEval(eval_frame, RuleBasedClassifier())
    eval.eval()
