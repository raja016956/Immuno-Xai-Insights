import pandas as pd
import numpy as np
import scanpy as sc
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix


# ============================================================
# DATASET LOADING
# ============================================================
def load_dataset(uploaded_file):
    """Load the uploaded expression dataset."""

    uploaded_file.seek(0)

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv.gz"):
        df = pd.read_csv(
            uploaded_file,
            compression="gzip",
            index_col=0
        )

    elif filename.endswith(".csv"):
        df = pd.read_csv(
            uploaded_file,
            index_col=0
        )

    else:
        raise ValueError(
            "Unsupported file format. Please upload a CSV or CSV.GZ file."
        )

    return df


# ============================================================
# DATASET INSPECTION
# ============================================================
def inspect_dataset(df):
    """Collect basic information about the expression dataset."""

    rows, columns = df.shape

    preview = df.head()

    first_genes = df.index[:10].tolist()

    first_samples = df.columns[:10].tolist()

    return {
        "rows": rows,
        "columns": columns,
        "preview": preview,
        "first_genes": first_genes,
        "first_samples": first_samples
    }


# ============================================================
# DATASET VALIDATION
# ============================================================
def validate_dataset(df):
    """Validate the structure and contents of the dataset."""

    if df.empty:
        raise ValueError(
            "The uploaded dataset is empty."
        )

    if df.index.empty:
        raise ValueError(
            "No gene identifiers were found."
        )

    if df.shape[1] < 2:
        raise ValueError(
            "The dataset must contain at least two samples."
        )

    if df.index.duplicated().any():

    # Merge duplicate gene identifiers by summing
    # their expression values across all samples.
        df = df.groupby(df.index).sum()

    if not all(
        pd.api.types.is_numeric_dtype(df[col])
        for col in df.columns
    ):
        raise ValueError(
            "Expression values must be numeric."
        )

    required_genes = [
        "CD3D",
        "CD3E",
        "GZMB",
        "CD274",
        "C1QA",
        "LST1",
        "CXCL9"
    ]

    missing_genes = [
        gene
        for gene in required_genes
        if gene not in df.index
    ]

    if missing_genes:
        raise ValueError(
            f"Required genes are missing: "
            f"{', '.join(missing_genes)}"
        )

    return df


# ============================================================
# DATAFRAME → ANNData
# ============================================================
def convert_to_anndata(df):
    """Convert the validated DataFrame into AnnData."""

    # AnnData expects:
    # rows = cells/samples
    # columns = genes
    adata = sc.AnnData(
        df.T.astype(np.float32)
    )

    # Assign gene identifiers
    adata.var_names = df.index

    # Assign sample/cell identifiers
    adata.obs_names = df.columns

    return adata


# ============================================================
# DATA PREPROCESSING
# ============================================================
def preprocess_data(adata):
    """Perform quality control, normalization, and log transformation."""

    # --------------------------------------------------------
    # 1. Calculate basic quality-control metrics
    # --------------------------------------------------------
    # --------------------------------------------------------
    # Calculate only the number of detected genes per cell
    # --------------------------------------------------------
    if sparse.issparse(adata.X):
        adata.obs["n_genes_by_counts"] = np.asarray(
            (adata.X > 0).sum(axis=1)
        ).ravel()
    else:
        adata.obs["n_genes_by_counts"] = (
            (adata.X > 0).sum(axis=1)
        )
    # --------------------------------------------------------
    # 2. Remove cells with very few detected genes
    # --------------------------------------------------------
    adata = adata[
        adata.obs["n_genes_by_counts"] >= 200
    ].copy()

    # --------------------------------------------------------
    # 3. Remove cells with unusually high gene counts
    # --------------------------------------------------------
    adata = adata[
        adata.obs["n_genes_by_counts"] <= 6000
    ].copy()

    # --------------------------------------------------------
    # 4. Remove genes detected in fewer than 3 cells
    # --------------------------------------------------------
    sc.pp.filter_genes(
        adata,
        min_cells=3
    )

    # --------------------------------------------------------
    # 5. Normalize each cell to 10,000 total counts
    # --------------------------------------------------------
    sc.pp.normalize_total(
        adata,
        target_sum=1e4
    )

    # --------------------------------------------------------
    # 6. Apply log transformation
    # --------------------------------------------------------
    sc.pp.log1p(adata)
    # --------------------------------------------------------
    # 7. Identify highly variable genes for ML
    # --------------------------------------------------------
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=2000,
        flavor="seurat"
    )

    return adata


# ============================================================
# PREPROCESSING VERIFICATION
# ============================================================
def verify_preprocessing(adata):
    """Verify that the preprocessed AnnData is valid."""

    # --------------------------------------------------------
    # 1. Check that cells and genes still exist
    # --------------------------------------------------------
    if adata.n_obs == 0:
        raise ValueError(
            "Preprocessing removed all cells/samples."
        )

    if adata.n_vars == 0:
        raise ValueError(
            "Preprocessing removed all genes."
        )

    # --------------------------------------------------------
    # 2. Check that required immune-marker genes remain
    # --------------------------------------------------------
    required_genes = [
        "CD3D",
        "CD3E",
        "GZMB",
        "CD274",
        "C1QA",
        "LST1",
        "CXCL9"
    ]

    missing_genes = [
        gene
        for gene in required_genes
        if gene not in adata.var_names
    ]

    if missing_genes:
        raise ValueError(
            "Required genes are missing after preprocessing: "
            + ", ".join(missing_genes)
        )

    # --------------------------------------------------------
    # 3. Get the expression matrix
    # --------------------------------------------------------
    expression = adata.X

    contains_invalid_values = False

    # --------------------------------------------------------
    # 4. Check sparse matrices
    # --------------------------------------------------------
    if sparse.issparse(expression):

        # Get the actual stored expression values
        values = np.asarray(expression.data)

        # Check for NaN or infinite values
        if not np.isfinite(values).all():
            contains_invalid_values = True

    # --------------------------------------------------------
    # 5. Check dense matrices in chunks
    # --------------------------------------------------------
    else:

        chunk_size = 500

        for start in range(
            0,
            adata.n_obs,
            chunk_size
        ):

            end = min(
                start + chunk_size,
                adata.n_obs
            )

            # Read one chunk of cells
            chunk = expression[start:end]

            # Check for NaN or infinite values
            if not np.isfinite(chunk).all():
                contains_invalid_values = True
                break

    # --------------------------------------------------------
    # 6. Stop if invalid values were found
    # --------------------------------------------------------
    if contains_invalid_values:
        raise ValueError(
            "The preprocessed dataset contains "
            "NaN or infinite values."
        )

    # --------------------------------------------------------
    # 7. Create verification results
    # --------------------------------------------------------
    verification = {
        "cells": adata.n_obs,
        "genes": adata.n_vars,
        "required_genes_present": True,
        "contains_invalid_values": False
    }

    return verification
# ============================================================
# IMMUNE SCORE CALCULATION
# ============================================================
def calculate_immune_scores(adata):
    """Calculate T-cell, PD-L1/myeloid, and immune-state scores."""

    # --------------------------------------------------------
    # 1. Define T-cell marker genes
    # --------------------------------------------------------
    tcell_genes = [
        "CD3D",
        "CD3E",
        "GZMB"
    ]

    # --------------------------------------------------------
    # 2. Define PD-L1/myeloid marker genes
    # --------------------------------------------------------
    pdl1_myeloid_genes = [
        "CD274",
        "C1QA",
        "LST1",
        "CXCL9"
    ]

    # --------------------------------------------------------
    # 3. Verify that all T-cell markers are available
    # --------------------------------------------------------
    missing_tcell_genes = [
        gene
        for gene in tcell_genes
        if gene not in adata.var_names
    ]

    if missing_tcell_genes:
        raise ValueError(
            "T-cell marker genes are missing: "
            + ", ".join(missing_tcell_genes)
        )

    # --------------------------------------------------------
    # 4. Verify that all PD-L1/myeloid markers are available
    # --------------------------------------------------------
    missing_pdl1_genes = [
        gene
        for gene in pdl1_myeloid_genes
        if gene not in adata.var_names
    ]

    if missing_pdl1_genes:
        raise ValueError(
            "PD-L1/myeloid marker genes are missing: "
            + ", ".join(missing_pdl1_genes)
        )

    # --------------------------------------------------------
    # 5. Calculate the T-cell score
    # --------------------------------------------------------
    sc.tl.score_genes(
        adata,
        gene_list=tcell_genes,
        score_name="Tcell_score",
        random_state=42
    )

    # --------------------------------------------------------
    # 6. Calculate the PD-L1/myeloid score
    # --------------------------------------------------------
    sc.tl.score_genes(
        adata,
        gene_list=pdl1_myeloid_genes,
        score_name="PDL1_myeloid_score",
        random_state=42
    )

    # --------------------------------------------------------
    # 7. Calculate the Immune State Index
    # --------------------------------------------------------
    adata.obs["Immune_State_Index"] = (
        adata.obs["Tcell_score"]
        - adata.obs["PDL1_myeloid_score"]
    )

    # Return the AnnData object with immune scores
    return adata

# ============================================================
# IMMUNE STATE LABELING
# ============================================================
def create_immune_state_labels(adata):
    """Assign immune-state labels using the Q25 and Q75 ISI thresholds."""

    # Get the Immune State Index
    isi = adata.obs["Immune_State_Index"]

    # Calculate dataset-specific thresholds
    q25 = isi.quantile(0.25)
    q75 = isi.quantile(0.75)

    # Assign immune-state labels
    adata.obs["Immune_State"] = "Intermediate"

    adata.obs.loc[
        isi <= q25,
        "Immune_State"
    ] = "Immune-Excluded"

    adata.obs.loc[
        isi >= q75,
        "Immune_State"
    ] = "Inflamed"

    return adata
# ============================================================
# IMMUNE STATE INDEX QUANTILES
# ============================================================
def calculate_isi_quantiles(adata):
    """Calculate descriptive quantiles for the Immune State Index."""

    isi = adata.obs["Immune_State_Index"]

    q25 = float(isi.quantile(0.25))
    median = float(isi.quantile(0.50))
    q75 = float(isi.quantile(0.75))

    low_count = int((isi <= q25).sum())
    middle_count = int(((isi > q25) & (isi < q75)).sum())
    high_count = int((isi >= q75).sum())

    adata.uns["isi_quantiles"] = {
        "q25": q25,
        "median": median,
        "q75": q75,
        "low_count": low_count,
        "middle_count": middle_count,
        "high_count": high_count
    }

    return adata

# ============================================================
# ML DATASET PREPARATION
# ============================================================
def prepare_ml_data(adata, n_top_genes=2000):
    """
    Prepare gene-expression features and immune-state labels
    for machine-learning classification.

    Input:
        adata: Preprocessed AnnData object.
        n_top_genes: Number of highly variable genes to retain.

    Returns:
        X: Gene-expression feature matrix.
        y: Binary immune-state labels.
        feature_names: Names of selected genes.
    """

    # --------------------------------------------------------
    # Keep only the two confident immune-state groups
    # --------------------------------------------------------
    ml_adata = adata[
        adata.obs["Immune_State"].isin(
            ["Immune-Excluded", "Inflamed"]
        )
    ].copy()

    # --------------------------------------------------------
    # Select the highly variable genes
    # --------------------------------------------------------
    ml_adata = ml_adata[
        :,
        ml_adata.var["highly_variable"]
    ].copy()

    # --------------------------------------------------------
    # Create feature matrix
    # --------------------------------------------------------
    X = ml_adata.X

    # Convert sparse matrix to dense array if necessary
    if sparse.issparse(X):
        X = X.toarray()

    # --------------------------------------------------------
    # Create binary target labels
    # --------------------------------------------------------
    y = (
        ml_adata.obs["Immune_State"]
        .map({
            "Immune-Excluded": 0,
            "Inflamed": 1
        })
        .to_numpy()
    )

    # --------------------------------------------------------
    # Store ML information for later stages
    # --------------------------------------------------------
    ml_info = {
        "samples": X.shape[0],
        "features": X.shape[1],
        "excluded_samples": int((y == 0).sum()),
        "inflamed_samples": int((y == 1).sum())
    }

    adata.uns["ml_info"] = ml_info

    return X, y, ml_adata.var_names.tolist()


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================
def create_train_test_split(X, y, test_size=0.20, random_state=42):
    """
    Split the ML dataset into training and testing sets.

    Input:
        X: Gene-expression feature matrix.
        y: Immune-state labels.
        test_size: Proportion reserved for testing.
        random_state: Seed for reproducibility.

    Returns:
        X_train: Training features.
        X_test: Testing features.
        y_train: Training labels.
        y_test: Testing labels.
    """

    # --------------------------------------------------------
    # Create stratified train/test split
    # --------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    return X_train, X_test, y_train, y_test



# ============================================================
# MODEL TRAINING
# ============================================================
def train_classifier(X_train, y_train):
    """
    Train a Logistic Regression classifier.

    Input:
        X_train: Training gene-expression features.
        y_train: Training immune-state labels.

    Returns:
        model: Trained Logistic Regression classifier.
    """

    # --------------------------------------------------------
    # Create the classification model
    # --------------------------------------------------------
    model = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    # --------------------------------------------------------
    # Train the model using training data only
    # --------------------------------------------------------
    model.fit(
        X_train,
        y_train
    )

    return model

# ============================================================
# FEATURE IMPORTANCE
# ============================================================
def calculate_feature_importance(model, feature_names, top_n=20):
    """
    Calculate global gene importance from Logistic Regression.

    Input:
        model: Trained Logistic Regression model.
        feature_names: Names of the genes used as features.
        top_n: Number of top genes to return.

    Returns:
        DataFrame containing the most important genes,
        their coefficients, and absolute importance.
    """

    # Get the model coefficient for each gene
    coefficients = model.coef_[0]

    # Create a table linking genes to their coefficients
    importance_df = pd.DataFrame({
        "Gene": feature_names,
        "Coefficient": coefficients,
        "Importance": np.abs(coefficients)
    })

    # Sort genes by their absolute importance
    importance_df = importance_df.sort_values(
        "Importance",
        ascending=False
    )

    # Keep only the top genes
    importance_df = importance_df.head(top_n).reset_index(drop=True)

    return importance_df

# ============================================================
# FEATURE IMPORTANCE
# ============================================================
def calculate_feature_importance(model, feature_names, top_n=20):
    """
    Calculate global gene importance from Logistic Regression.

    Input:
        model: Trained Logistic Regression model.
        feature_names: Names of the genes used as features.
        top_n: Number of top genes to return.

    Returns:
        DataFrame containing the top important genes,
        their coefficients, and absolute importance.
    """

    # Get the coefficient for each gene
    coefficients = model.coef_[0]

    # Create a table connecting genes with their coefficients
    importance_df = pd.DataFrame({
        "Gene": feature_names,
        "Coefficient": coefficients,
        "Importance": np.abs(coefficients)
    })

    # Sort genes by absolute importance
    importance_df = importance_df.sort_values(
        "Importance",
        ascending=False
    )

    # Keep only the top important genes
    importance_df = importance_df.head(top_n).reset_index(drop=True)

    return importance_df


# ============================================================
# MODEL EVALUATION
# ============================================================
def evaluate_classifier(model, X_test, y_test):
    """
    Evaluate the trained classifier on unseen test data.

    Input:
        model: Trained classification model.
        X_test: Unseen testing features.
        y_test: True testing labels.

    Returns:
        evaluation: Dictionary containing predictions,
                    classification metrics, and confusion matrix.
    """

    # --------------------------------------------------------
    # Generate predictions on unseen test data
    # --------------------------------------------------------
    y_pred = model.predict(X_test)

    # --------------------------------------------------------
    # Calculate classification metrics
    # --------------------------------------------------------
    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )

    # --------------------------------------------------------
    # Calculate confusion matrix
    # --------------------------------------------------------
    cm = confusion_matrix(
        y_test,
        y_pred
    )

    # --------------------------------------------------------
    # Store all evaluation results
    # --------------------------------------------------------
    evaluation = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm,
        "predictions": y_pred
    }

    # --------------------------------------------------------
    # Return evaluation results
    # --------------------------------------------------------
    return evaluation

# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline(uploaded_file):
    """Run the complete dataset processing pipeline."""

    # 1. Load the uploaded dataset
    df = load_dataset(uploaded_file)

    # 2. Inspect the original dataset
    inspection = inspect_dataset(df)

    # 3. Validate the dataset
    df = validate_dataset(df)

    # 4. Convert DataFrame to AnnData
    adata = convert_to_anndata(df)

    # 5. Preprocess the expression data
    adata = preprocess_data(adata)

    # 6. Verify the preprocessing result
    verification = verify_preprocessing(adata)
    
    # 7. Calculate immune scores
    adata = calculate_immune_scores(adata)

    # 8. Calculate Immune State Index quantiles
    adata = calculate_isi_quantiles(adata)

    # 9. Create immune-state labels
    adata = create_immune_state_labels(adata)

    # 10. Prepare features and labels for machine learning
    X, y, feature_names = prepare_ml_data(adata)

    # --------------------------------------------------------
    # Create reproducible training and testing datasets
    # --------------------------------------------------------
    X_train, X_test, y_train, y_test = create_train_test_split(
        X,
        y
    )

    # --------------------------------------------------------
    # Train the baseline classifier
    # --------------------------------------------------------
    model = train_classifier(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Calculate global gene feature importance
    # --------------------------------------------------------
    feature_importance = calculate_feature_importance(
        model,
        feature_names,
        top_n=20
    )

    # --------------------------------------------------------
    # Store feature importance for the analysis page
    # --------------------------------------------------------
    adata.uns["feature_importance"] = feature_importance


    # --------------------------------------------------------
    # Store feature importance for the analysis page
    # --------------------------------------------------------
    adata.uns["feature_importance"] = feature_importance

    # --------------------------------------------------------
    # Calculate global gene feature importance
    # --------------------------------------------------------
    feature_importance = calculate_feature_importance(
        model,
        feature_names,
        top_n=20
    )

    # --------------------------------------------------------
    # Store feature importance for the analysis page
    # --------------------------------------------------------
    adata.uns["feature_importance"] = feature_importance

    # --------------------------------------------------------
    # Evaluate the trained classifier on unseen test data
    # --------------------------------------------------------
    evaluation = evaluate_classifier(
        model,
        X_test,
        y_test
    )

    # --------------------------------------------------------
    # Store model evaluation results
    # --------------------------------------------------------
    adata.uns["model_evaluation"] = {
        "accuracy": evaluation["accuracy"],
        "precision": evaluation["precision"],
        "recall": evaluation["recall"],
        "f1_score": evaluation["f1_score"],
        "confusion_matrix": evaluation["confusion_matrix"]
    }

    # --------------------------------------------------------
    # Store ML split information for later pipeline stages
    # --------------------------------------------------------
    adata.uns["ml_split_info"] = {
        "train_samples": X_train.shape[0],
        "test_samples": X_test.shape[0],
        "train_features": X_train.shape[1],
        "test_features": X_test.shape[1],
        "train_excluded": int((y_train == 0).sum()),
        "train_inflamed": int((y_train == 1).sum()),
        "test_excluded": int((y_test == 0).sum()),
        "test_inflamed": int((y_test == 1).sum())
    }

    # --------------------------------------------------------
    # Return all pipeline results
    # --------------------------------------------------------
    
    return adata, inspection, verification