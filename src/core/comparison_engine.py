import pandas as pd
from rapidfuzz import fuzz
import warnings
from datetime import datetime
from time import time
import numpy as np
import soundex

class ComparisonEngine:
    """Enhanced engine with multiple comparison methods for maximum accuracy"""
    
    def __init__(self, key_columns=None, value_columns=None, fuzzy_threshold=100):
        # Default key columns (B, C, D)
        self.key_columns = key_columns or ["Serie", "Locomotive", "CodeOp"]
        # Default value columns (E-J)
        self.value_columns = value_columns or [
            "Commentaire", "Date Butee", "Date programmation",
            "Heure programmation", "Date sortie", "Heure sortie"
        ]
        # Fuzzy threshold (0-100), 100 = exact match
        self.fuzzy_threshold = fuzzy_threshold
        
        # Enhanced comparison settings
        self.comparison_methods = {
            'exact': {'weight': 0.3, 'enabled': True},
            'fuzzy': {'weight': 0.25, 'enabled': True},  
            'semantic': {'weight': 0.15, 'enabled': True},
            'phonetic': {'weight': 0.1, 'enabled': True},
            'date': {'weight': 0.2, 'enabled': True}
        }

        self.confidence_thresholds = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
    
    def set_dynamic_value_columns(self, base_df, comp_df):
        """Dynamically set value columns based on what's available in both DataFrames"""
        base_cols = set(base_df.columns)
        comp_cols = set(comp_df.columns)
        
        # Find common columns that are not key columns
        common_cols = base_cols & comp_cols
        available_value_cols = [col for col in self.value_columns if col in common_cols]
        
        # If no predefined value columns are available, use all non-key columns
        if not available_value_cols:
            all_cols = list(common_cols)
            available_value_cols = [col for col in all_cols if col not in self.key_columns and col != 'Site']
        
        # print(f"Using value columns: {available_value_cols}")
        return available_value_cols

    def prepare(self, df):
        """Clean and convert DataFrame columns"""
        df = df.copy().fillna("")
        df.columns = pd.Index([f"{col}_{i}" if df.columns[:i+1].tolist().count(col) > 1 else col 
                              for i, col in enumerate(df.columns)])
        
        # print(f"After handling duplicates: {df.columns.tolist()}")
        
        for col in df.columns:
            try:
                # Check if this column access returns a Series (not a DataFrame)
                col_data = df[col]
                if isinstance(col_data, pd.DataFrame):
                    print(f"Warning: Column '{col}' returns DataFrame, skipping processing")
                    continue
                    
                if col in self.key_columns:
                    df[col] = col_data.astype(str).str.strip()
                    continue
                
                # Convert all to string and strip whitespace
                df[col] = col_data.astype(str).str.strip()
                
                # Attempt datetime parsing, suppress warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    try:
                        df[col] = pd.to_datetime(col_data, infer_datetime_format=True, dayfirst=True)
                    except (ValueError, TypeError):
                        pass
                
                if df[col].dtype == object:
                    try:
                        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"Error processing column '{col}': {e}")
                continue
        
        df = df.replace({pd.NaT: "", "NaT": "", "nan": "", None: ""})
        df = df.fillna("")
        return df

    def normalize_key(self, df):
        """Build composite key column from key_columns"""
        df = df.copy()
        
        # Debug to see available columns
        # print(f"Available columns: {df.columns.tolist()}")
        # print(f"Looking for key columns: {self.key_columns}")
        
        # Check which key columns actually exist in the DataFrame
        available_key_cols = [col for col in self.key_columns if col in df.columns]
        
        # print(f"Found available key columns: {available_key_cols}")
        
        # If no key columns exist, add a placeholder column
        if not available_key_cols:
            print("WARNING: No key columns found. Using row numbers as keys.")
            df['key'] = range(len(df))
            return df
        
        # Normalize Locomotive if it exists
        if 'Locomotive' in df.columns:
            df['Locomotive'] = df['Locomotive'].astype(str).str.upper().str.replace(r'\s+', '', regex=True)
        
        # Clean up available key columns only
        for col in available_key_cols:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
        
        # Create composite key from available columns only
        df['key'] = df[available_key_cols].astype(str).agg('_'.join, axis=1)
        
        return df

    def find_differences(self, base_df, comp_df):
        """
        Returns DataFrame of added, removed, and modified rows between two DataFrames.
        Columns: Key, Column (if modified), Base Value, Comparison Value, Status
        Status ∈ {Ajoutée, Supprimée, Modifiée}
        """
        base = self.normalize_key(self.prepare(base_df)).reset_index(drop=True)
        comp = self.normalize_key(self.prepare(comp_df)).reset_index(drop=True)
        base['Base Row'] = base.index + 3
        comp['Comp Row'] = comp.index + 8

        # Only use value columns that exist in both DataFrames
        base_value_cols = [col for col in self.value_columns if col in base.columns]
        comp_value_cols = [col for col in self.value_columns if col in comp.columns]
        common_value_cols = list(set(base_value_cols) & set(comp_value_cols))
        
        # print(f"Base value columns available: {base_value_cols}")
        # print(f"Comp value columns available: {comp_value_cols}")
        # print(f"Common value columns: {common_value_cols}")

        merged = (
            base.set_index('key')[common_value_cols + ['Base Row']]
            .join(comp.set_index('key')[common_value_cols + ['Comp Row']], how='outer',
                  lsuffix='_base', rsuffix='_comp', sort=False)
            .reset_index()
        )
        results = []
        base_keys = set(base['key'])
        comp_keys = set(comp['key'])

        for _, row in merged.iterrows():
            key = row['key']
            in_base = key in base_keys
            in_comp = key in comp_keys
            base_row = row.get('Base Row', '')
            comp_row = row.get('Comp Row', '')
            # Added or removed
            if not in_base and in_comp:
                results.append({'Key': key, 'Status': 'Ajoutée', 'Base Row': '', 'Comp Row': comp_row})
            elif in_base and not in_comp:
                results.append({'Key': key, 'Status': 'Supprimée', 'Base Row': base_row, 'Comp Row': ''})
            else:
                # Compare each common value column only
                for col in common_value_cols:
                    vb = row[f'{col}_base']
                    vc = row[f'{col}_comp']
                    if pd.isna(vb) and pd.isna(vc):
                        continue
                    if vb == vc:
                        continue
                    # Fuzzy match for strings
                    if isinstance(vb, str) and isinstance(vc, str):
                        if fuzz.ratio(vb, vc) >= self.fuzzy_threshold:
                            continue
                    results.append({
                        'Key': key,
                        'Column': col,
                        'Base Value': vb,
                        'Comparison Value': vc,
                        'Status': 'Modifiée',
                        'Base Row': base_row,
                        'Comp Row': comp_row
                    })
        return pd.DataFrame(results)

    def find_duplicates(self, df, source='base'):
        data = self.normalize_key(self.prepare(df)).reset_index(drop=True)
        row_col = 'Base Row' if source == 'base' else 'Comp Row'
        data[row_col] = data.index + 3
        dup_keys = data['key'][data['key'].duplicated(keep=False)].unique()

        available_cols = [col for col in data.columns if col in data.columns]
        return data[data['key'].isin(dup_keys)][available_cols].sort_values('key')

    def compare_with_multiple_methods(self, base_df, comp_df, mode='full'):
        """
        Enhanced comparison using multiple methods but with prioritized, filtered results
        """
        dynamic_value_cols = self.set_dynamic_value_columns(base_df, comp_df)
        print(f"Enhanced comparison mode: {mode}")
        original_value_cols = self.value_columns
        self.value_columns = dynamic_value_cols

        try:
            # Disable date comparison as requested
            self.comparison_methods['date']['enabled'] = False
            
            # Get results from each method
            methods_results = {}
            
            # Method 1: Exact matching (current method)
            if self.comparison_methods['exact']['enabled']:
                methods_results['exact'] = self._exact_comparison(base_df, comp_df)
            
            # Method 2: Fuzzy matching with multiple algorithms
            if self.comparison_methods['fuzzy']['enabled']:
                methods_results['fuzzy'] = self._fuzzy_comparison(base_df, comp_df)
            
            # Method 3: Semantic comparison for text fields
            if self.comparison_methods['semantic']['enabled']:
                methods_results['semantic'] = self._semantic_comparison(base_df, comp_df)
            
            # Method 4: Phonetic comparison for names/codes
            if self.comparison_methods['phonetic']['enabled']:
                methods_results['phonetic'] = self._phonetic_comparison(base_df, comp_df)
            
            # Prioritize and filter results to get only the most relevant ones
            final_results = self._prioritize_results(methods_results)
            
            # Return based on mode
            if mode == 'summary':
                return self._create_enhanced_summary(final_results)
            else:
                return self._format_enhanced_results(final_results, mode)
                
        finally:
            self.value_columns = original_value_cols

    def _prioritize_results(self, methods_results):
        """Prioritize results to return only the most relevant differences"""
        exact_differences = methods_results.get('exact', {}).get('differences', pd.DataFrame())

        reported_keys = set()
        if not exact_differences.empty:
            for _, row in exact_differences.iterrows():
                if 'Key' in row:
                    reported_keys.add(row['Key'])
        
        # Create a list to hold all prioritized differences
        all_differences = []

        if not exact_differences.empty:
            for _, diff in exact_differences.iterrows():
                diff_dict = diff.to_dict()
                diff_dict['method'] = 'exact'
                diff_dict['confidence'] = 1.0
                all_differences.append(diff_dict)

        fuzzy_differences = methods_results.get('fuzzy', {}).get('differences', pd.DataFrame())
        if not fuzzy_differences.empty:
            for _, diff in fuzzy_differences.iterrows():
                if 'similarity' in diff and diff['similarity'] >= 90:
                    base_key = diff.get('base_key', '')
                    comp_key = diff.get('comp_key', '')

                    if base_key in reported_keys or comp_key in reported_keys:
                        continue
                    
                    diff_dict = diff.to_dict()
                    diff_dict['method'] = 'fuzzy'
                    diff_dict['Status'] = 'Similaire'
                    all_differences.append(diff_dict)
                    reported_keys.add(base_key)
                    reported_keys.add(comp_key)

        semantic_differences = methods_results.get('semantic', {}).get('differences', pd.DataFrame())
        if not semantic_differences.empty:
            for _, diff in semantic_differences.iterrows():
                if 'semantic_score' in diff and diff['semantic_score'] >= 70:
                    base_key = diff.get('base_key', '')
                    comp_key = diff.get('comp_key', '')
                    
                    if base_key in reported_keys or comp_key in reported_keys:
                        continue
                    
                    diff_dict = diff.to_dict()
                    diff_dict['method'] = 'semantic'
                    diff_dict['Status'] = 'Contenu Similaire'
                    all_differences.append(diff_dict)
                    reported_keys.add(base_key)
                    reported_keys.add(comp_key)

        phonetic_differences = methods_results.get('phonetic', {}).get('differences', pd.DataFrame())
        if not phonetic_differences.empty:
            for _, diff in phonetic_differences.iterrows():
                base_key = diff.get('base_key', '')
                comp_key = diff.get('comp_key', '')
                
                if base_key in reported_keys or comp_key in reported_keys:
                    continue
                
                diff_dict = diff.to_dict()
                diff_dict['method'] = 'phonetic'
                diff_dict['Status'] = 'Orthographe Similaire'
                all_differences.append(diff_dict)
                reported_keys.add(base_key)
                reported_keys.add(comp_key)
        
        # Return the prioritized results
        return {
            'differences': pd.DataFrame(all_differences),
            'duplicates_base': methods_results.get('exact', {}).get('duplicates_base', pd.DataFrame()),
            'duplicates_comp': methods_results.get('exact', {}).get('duplicates_comp', pd.DataFrame()),
            'method_breakdown': methods_results
        }

    def _exact_comparison(self, base_df, comp_df):
        """Exact matching method (your current implementation)"""
        return {
            'differences': self.find_differences(base_df, comp_df),
            'duplicates_base': self.find_duplicates(base_df, source='base'),
            'duplicates_comp': self.find_duplicates(comp_df, source='comp'),
            'method': 'exact',
            'confidence': 1.0
        }
    
    def _fuzzy_comparison(self, base_df, comp_df):
        """Enhanced fuzzy matching with multiple algorithms"""
        base = self.normalize_key(self.prepare(base_df)).reset_index(drop=True)
        comp = self.normalize_key(self.prepare(comp_df)).reset_index(drop=True)
        
        # Multiple fuzzy algorithms
        fuzzy_algorithms = {
            'ratio': fuzz.ratio,
            'partial_ratio': fuzz.partial_ratio,
            'token_sort_ratio': fuzz.token_sort_ratio,
            'token_set_ratio': fuzz.token_set_ratio
        }
        
        fuzzy_results = []
        
        for _, base_row in base.iterrows():
            for _, comp_row in comp.iterrows():
                # Calculate similarities for each value column
                similarities = {}
                overall_similarity = 0
                
                for col in self.value_columns:
                    if col in base.columns and col in comp.columns:
                        base_val = str(base_row[col])
                        comp_val = str(comp_row[col])
                        
                        # Calculate similarity using multiple algorithms
                        col_similarities = {}
                        for alg_name, alg_func in fuzzy_algorithms.items():
                            col_similarities[alg_name] = alg_func(base_val, comp_val)
                        
                        # Average similarity for this column
                        similarities[col] = sum(col_similarities.values()) / len(col_similarities)
                        overall_similarity += similarities[col]
                
                # Average overall similarity
                if similarities:
                    overall_similarity /= len(similarities)
                    
                    # If similarity is between thresholds, it's a potential match
                    if 50 <= overall_similarity < self.fuzzy_threshold:
                        fuzzy_results.append({
                            'base_key': base_row['key'],
                            'comp_key': comp_row['key'],
                            'similarity': overall_similarity,
                            'column_similarities': similarities,
                            'match_type': 'fuzzy_match'
                        })
        
        return {
            'differences': pd.DataFrame(fuzzy_results),
            'duplicates_base': self.find_duplicates(base_df, source='base'),
            'duplicates_comp': self.find_duplicates(comp_df, source='comp'),
            'method': 'fuzzy',
            'confidence': 0.8
        }
    
    def _semantic_comparison(self, base_df, comp_df):
        """Semantic comparison for text fields"""
        try:
            # Simple semantic comparison using word overlap
            base = self.normalize_key(self.prepare(base_df)).reset_index(drop=True)
            comp = self.normalize_key(self.prepare(comp_df)).reset_index(drop=True)
            
            semantic_results = []
            
            # Focus on text columns (like Commentaire)
            text_columns = [col for col in self.value_columns 
                          if col in base.columns and col in comp.columns 
                          and col in ['Commentaire', 'Libelle', 'Description']]
            
            for _, base_row in base.iterrows():
                for _, comp_row in comp.iterrows():
                    semantic_scores = {}
                    
                    for col in text_columns:
                        base_text = str(base_row[col]).lower()
                        comp_text = str(comp_row[col]).lower()
                        
                        # Word overlap semantic similarity
                        base_words = set(base_text.split())
                        comp_words = set(comp_text.split())
                        
                        if base_words or comp_words:
                            intersection = len(base_words & comp_words)
                            union = len(base_words | comp_words)
                            jaccard_similarity = intersection / union if union > 0 else 0
                            semantic_scores[col] = jaccard_similarity * 100
                    
                    if semantic_scores:
                        avg_semantic = sum(semantic_scores.values()) / len(semantic_scores)
                        if avg_semantic > 30:  # Threshold for semantic similarity
                            semantic_results.append({
                                'base_key': base_row['key'],
                                'comp_key': comp_row['key'],
                                'semantic_score': avg_semantic,
                                'column_scores': semantic_scores,
                                'match_type': 'semantic_match'
                            })
            
            return {
                'differences': pd.DataFrame(semantic_results),
                'duplicates_base': pd.DataFrame(),
                'duplicates_comp': pd.DataFrame(),
                'method': 'semantic',
                'confidence': 0.6
            }
            
        except Exception as e:
            print(f"Semantic comparison failed: {e}")
            return {
                'differences': pd.DataFrame(),
                'duplicates_base': pd.DataFrame(),
                'duplicates_comp': pd.DataFrame(),
                'method': 'semantic',
                'confidence': 0.0
            }
    
    def _phonetic_comparison(self, base_df, comp_df):
        """Phonetic comparison for names and codes"""
        try:           
            base = self.normalize_key(self.prepare(base_df)).reset_index(drop=True)
            comp = self.normalize_key(self.prepare(comp_df)).reset_index(drop=True)
            
            phonetic_results = []
            
            # Focus on name-like columns
            name_columns = [col for col in self.value_columns 
                          if col in base.columns and col in comp.columns 
                          and col in ['Serie', 'Locomotive', 'CodeOp']]
            
            for _, base_row in base.iterrows():
                for _, comp_row in comp.iterrows():
                    phonetic_matches = {}
                    
                    for col in name_columns:
                        base_val = str(base_row[col])
                        comp_val = str(comp_row[col])
                        
                        # Soundex comparison
                        try:
                            base_soundex = soundex.soundex(base_val)
                            comp_soundex = soundex.soundex(comp_val)
                            
                            if base_soundex == comp_soundex and base_val != comp_val:
                                phonetic_matches[col] = {
                                    'base_value': base_val,
                                    'comp_value': comp_val,
                                    'soundex_code': base_soundex
                                }
                        except:
                            pass
                    
                    if phonetic_matches:
                        phonetic_results.append({
                            'base_key': base_row['key'],
                            'comp_key': comp_row['key'],
                            'phonetic_matches': phonetic_matches,
                            'match_type': 'phonetic_match'
                        })
            
            return {
                'differences': pd.DataFrame(phonetic_results),
                'duplicates_base': pd.DataFrame(),
                'duplicates_comp': pd.DataFrame(),
                'method': 'phonetic',
                'confidence': 0.7
            }
            
        except ImportError:
            print("Soundex library not available, skipping phonetic comparison")
            return {
                'differences': pd.DataFrame(),
                'duplicates_base': pd.DataFrame(),
                'duplicates_comp': pd.DataFrame(),
                'method': 'phonetic',
                'confidence': 0.0
            }
        
    def _aggregate_results(self, methods_results):
        """Aggregate results from multiple methods with confidence weighting"""
        aggregated = {
            'differences': [],
            'duplicates_base': [],
            'duplicates_comp': [],
            'method_breakdown': methods_results,
            'confidence_scores': {},
            'consensus_results': []
        }
        
        # Combine all differences with confidence scoring
        all_differences = []
        
        for method_name, results in methods_results.items():
            method_weight = self.comparison_methods[method_name]['weight']
            method_confidence = results['confidence']
            
            # Process differences
            if not results['differences'].empty:
                for _, diff in results['differences'].iterrows():
                    diff_dict = diff.to_dict()
                    diff_dict['method'] = method_name
                    diff_dict['confidence'] = method_confidence * method_weight
                    diff_dict['weighted_confidence'] = method_confidence * method_weight
                    all_differences.append(diff_dict)
        
        # Group by key and find consensus
        key_groups = {}
        for diff in all_differences:
            key = diff.get('Key', diff.get('base_key', 'unknown'))
            if key not in key_groups:
                key_groups[key] = []
            key_groups[key].append(diff)
        
        # Calculate consensus for each key
        consensus_results = []
        for key, diffs in key_groups.items():
            if len(diffs) >= 2:  # Consensus requires at least 2 methods
                avg_confidence = sum(d['confidence'] for d in diffs) / len(diffs)
                consensus_results.append({
                    'key': key,
                    'methods_agreeing': len(diffs),
                    'average_confidence': avg_confidence,
                    'confidence_level': self._get_confidence_level(avg_confidence),
                    'details': diffs
                })
        aggregated['differences'] = pd.DataFrame(all_differences)
        aggregated['consensus_results'] = consensus_results
        
        return aggregated
    
    def _get_confidence_level(self, confidence):
        """Get confidence level string"""
        if confidence >= self.confidence_thresholds['high']:
            return 'HIGH'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'MEDIUM'
        elif confidence >= self.confidence_thresholds['low']:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _create_enhanced_summary(self, aggregated_results):
        """Create enhanced summary with method breakdown"""
        method_breakdown = {}
        
        for method_name, results in aggregated_results['method_breakdown'].items():
            method_breakdown[method_name] = {
                'total_diffs': len(results['differences']),
                'total_dups_base': len(results['duplicates_base']),
                'total_dups_comp': len(results['duplicates_comp']),
                'confidence': results['confidence']
            }
        
        return {
            'total_diffs': len(aggregated_results['differences']),
            'total_dups_base': sum(len(r['duplicates_base']) for r in aggregated_results['method_breakdown'].values()),
            'total_dups_comp': sum(len(r['duplicates_comp']) for r in aggregated_results['method_breakdown'].values()),
            'method_breakdown': method_breakdown,
            'consensus_count': len(aggregated_results['consensus_results']),
            'high_confidence_count': len([r for r in aggregated_results['consensus_results'] 
                                        if r['confidence_level'] == 'HIGH']),
            'medium_confidence_count': len([r for r in aggregated_results['consensus_results'] 
                                          if r['confidence_level'] == 'MEDIUM']),
            'low_confidence_count': len([r for r in aggregated_results['consensus_results'] 
                                       if r['confidence_level'] == 'LOW'])
        }
    
    def _format_enhanced_results(self, aggregated_results, mode):
        """Format enhanced results for different modes"""
        # Get simplified, exploitable results
        simplified_differences = self.get_simplified_results(aggregated_results['differences'])
        
        if mode == 'differences-only':
            return simplified_differences, pd.DataFrame(), pd.DataFrame()
        else:
            # Full mode - include everything
            dups_base = aggregated_results['duplicates_base']
            dups_comp = aggregated_results['duplicates_comp']
            return simplified_differences, dups_base, dups_comp
    
    def get_simplified_results(self, results_df):
        """
        Format results in a more exploitable way, focusing on actionable differences
        """
        if results_df.empty:
            return pd.DataFrame()

        simplified = []
        
        for _, row in results_df.iterrows():
            method = row.get('method', 'unknown')
            
            if method == 'exact':
                simplified.append({
                    'Key': row.get('Key', ''),
                    'Status': row.get('Status', ''),
                    'Column': row.get('Column', ''),
                    'Base Value': row.get('Base Value', ''),
                    'Comparison Value': row.get('Comparison Value', ''),
                    'Base Row': row.get('Base Row', ''),
                    'Comp Row': row.get('Comp Row', ''),
                    'Method': 'Exact',
                    'Confidence': 'High'
                })
            
            elif method == 'fuzzy':
                # Format fuzzy matches
                similarity = row.get('similarity', 0)
                confidence = 'High' if similarity >= 90 else 'Medium' if similarity >= 80 else 'Low'
                
                simplified.append({
                    'Key': f"{row.get('base_key', '')} ≈ {row.get('comp_key', '')}",
                    'Status': 'Similaire',
                    'Column': str(row.get('column_similarities', {})),
                    'Base Value': row.get('base_key', ''),
                    'Comparison Value': row.get('comp_key', ''),
                    'Base Row': '',
                    'Comp Row': '',
                    'Method': 'Fuzzy',
                    'Confidence': confidence,
                    'Similarity': f"{similarity:.1f}%"
                })
            
            elif method in ['semantic', 'phonetic']:
                # Format semantic and phonetic matches
                simplified.append({
                    'Key': f"{row.get('base_key', '')} ~ {row.get('comp_key', '')}",
                    'Status': 'Contenu Similaire' if method == 'semantic' else 'Orthographe Similaire',
                    'Column': '',
                    'Base Value': row.get('base_key', ''),
                    'Comparison Value': row.get('comp_key', ''),
                    'Base Row': '',
                    'Comp Row': '',
                    'Method': method.capitalize(),
                    'Confidence': 'Medium'
                })
        
        return pd.DataFrame(simplified)
    
    def compare(self, base_df, comp_df, mode='full'):
        """
        Main comparison method - routes to enhanced or standard comparison
        """
        try:
            # Try enhanced comparison first
            return self.compare_with_multiple_methods(base_df, comp_df, mode)
        except Exception as e:
            print(f"Enhanced comparison failed, falling back to standard: {e}")
            # Fallback to your existing implementation
            return self._standard_comparison(base_df, comp_df, mode)
    
    def _standard_comparison(self, base_df, comp_df, mode='full'):
        """Your existing comparison logic as fallback"""
        dynamic_value_cols = self.set_dynamic_value_columns(base_df, comp_df)
        original_value_cols = self.value_columns
        self.value_columns = dynamic_value_cols

        try:
            diffs = pd.DataFrame()
            dups_base = pd.DataFrame()
            dups_comp = pd.DataFrame()
                
            if mode == 'summary':
                diffs = self.find_differences(base_df, comp_df)
                dups_base = self.find_duplicates(base_df, source='base')
                dups_comp = self.find_duplicates(comp_df, source='comp')
                
                # Return only summary statistics
                summary = {
                    'total_diffs': len(diffs),
                    'total_dups_base': len(dups_base),
                    'total_dups_comp': len(dups_comp)
                }
                return summary

            if mode in ['full', 'differences-only']:
                diffs = self.find_differences(base_df, comp_df)
            if mode == 'full':
                dups_base = self.find_duplicates(base_df, source='base')
                dups_comp = self.find_duplicates(comp_df, source='comp')

            return diffs, dups_base, dups_comp
        
        finally:
            self.value_columns = original_value_cols

    @staticmethod
    def run_comparison(session_data, ExcelProcessor, safe_convert_func):
        settings = session_data['comparison_settings']
        mode = settings.get('comparison_mode', 'full')

        engine = ComparisonEngine(fuzzy_threshold=100)
        all_results = {}
        total = {'diffs': 0, 'dups': 0, 'cells': 0}
        start = time()
        
        for sheet in settings['selected_sheets']:
            bp = ExcelProcessor(settings['base_file'].file_path)
            if not bp.load_workbook(): continue
            df_base = bp.get_sheet_data(sheet, is_base_file=True, use_dynamic_detection=True)
            if df_base.empty:
                all_results[sheet] = []
                continue
                
            sheet_out = []
            for comp_info in settings['comparison_files']:
                cp = ExcelProcessor(comp_info.file_path)
                if not cp.load_workbook() or not cp.sheet_names: continue
                
                # Find matching sheet or use first available
                target_sheet = sheet
                if target_sheet not in cp.sheet_names and cp.sheet_names:
                    # Try to match by site code
                    if settings['site_mappings']:
                        for code, mapped_sheet in settings['site_mappings'].items():
                            if mapped_sheet == sheet and any(code in s for s in cp.sheet_names):
                                matched_sheets = [s for s in cp.sheet_names if code in s]
                                if matched_sheets:
                                    target_sheet = matched_sheets[0]
                                    break
                    
                    # If still no match, use first sheet
                    if target_sheet not in cp.sheet_names:
                        target_sheet = cp.sheet_names[0]
                
                df_comp = cp.get_sheet_data(target_sheet, is_base_file=False, use_dynamic_detection=True)
                if df_comp.empty: continue
                
                # Apply site filtering if configured
                if settings['site_mappings']:
                    codes = list(settings['site_mappings'].keys())
                    df_comp = df_comp[df_comp['Site'].str.contains('|'.join(codes), case=False, na=False, regex=True)]
                    if df_comp.empty: continue
                
                # Cell count
                total['cells'] += len(df_base) * len(engine.value_columns)
                
                # Core compare
                compare_result = engine.compare(df_base, df_comp, mode=mode)
                
                if mode == 'summary':
                    # In summary mode, we get back only a dictionary with counts
                    file_summary = compare_result
                    total['diffs'] += file_summary.get('total_diffs', 0)
                    total['dups'] += (file_summary.get('total_dups_base', 0) + 
                                    file_summary.get('total_dups_comp', 0))
                    sheet_out.append({
                        'comparison_file': comp_info.file_name,
                        'base_rows': int(len(df_base)),
                        'comp_rows': int(len(df_comp)),
                        'summary': file_summary
                    })
                else:
                    # In full or differences-only mode, we get the DataFrames
                    diffs, dups_base, dups_comp = compare_result
                    
                    # Update totals
                    if len(diffs) > 0 or len(dups_base) > 0 or len(dups_comp) > 0:
                        total['diffs'] += len(diffs)
                        total['dups'] += len(dups_base) + len(dups_comp)
                    
                    # Add full data to results
                    sheet_out.append({
                        'comparison_file': comp_info.file_name,
                        'differences': safe_convert_func(diffs.fillna('').to_dict('records')),
                        'differences_columns': safe_convert_func(diffs.columns.tolist()),
                        'duplicates_base': safe_convert_func(dups_base.fillna('').to_dict('records')),
                        'duplicates_base_columns': safe_convert_func(dups_base.columns.tolist()),
                        'duplicates_comp': safe_convert_func(dups_comp.fillna('').to_dict('records')),
                        'duplicates_comp_columns': safe_convert_func(dups_comp.columns.tolist()),
                        'base_rows': int(len(df_base)),
                        'comp_rows': int(len(df_comp))
                    })
            
            all_results[sheet] = sheet_out

        summary = {
            'total_sheets_compared': len(settings['selected_sheets']),
            'total_cells_compared': total['cells'] or 1,
            'total_differences': total['diffs'],
            'total_duplicates': total['dups'],
            'execution_time_seconds': time() - start
        }

        session_data['comparison_results'] = {
            'results': all_results, 
            'summary': summary, 
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            'results': all_results, 
            'summary': summary, 
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
