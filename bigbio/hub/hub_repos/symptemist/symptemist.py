# coding=utf-8
# Copyright 2022 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from typing import Dict, List, Tuple

import datasets
import pandas as pd

from .bigbiohub import kb_features
from .bigbiohub import BigBioConfig
from .bigbiohub import Tasks

_LANGUAGES = ['Spanish']
_PUBMED = False
_LOCAL = False
_CITATION = """\
"""

_DATASETNAME = "symptemist"
_DISPLAYNAME = "SympTEMIST"

_DESCRIPTION = """\
The SympTEMIST corpus is a collection of 1,000 clinical case reports in Spanish annotated with symptoms, signs and findings mentions and normalized to SNOMED CT. The texts belong to the SPACCC corpus and are the same ones used in SympTEMIST and MedProcNER, making the annotations complementary for medical entity recognition.
"""

_HOMEPAGE = "https://temu.bsc.es/symptemist/"

_LICENSE = 'CC_BY_4p0'

_URLS = {
    _DATASETNAME: "https://zenodo.org/record/8358431/files/symptemist-train_all_subtasks%2Bgazetteer%2Bmultilingual_230919.zip?download=1",
}

_SUPPORTED_TASKS = [Tasks.NAMED_ENTITY_RECOGNITION, Tasks.NAMED_ENTITY_DISAMBIGUATION]

_SOURCE_VERSION = "1.0.0"
_BIGBIO_VERSION = "2.0.0"


class SymptemistDataset(datasets.GeneratorBasedBuilder):
    """
    The SympTEMIST corpus is a collection of 1,000 clinical case reports in Spanish annotated with symptoms, signs and findings mentions and normalized to SNOMED CT.
    """

    SOURCE_VERSION = datasets.Version(_SOURCE_VERSION)
    BIGBIO_VERSION = datasets.Version(_BIGBIO_VERSION)

    BUILDER_CONFIGS = [
        BigBioConfig(
            name="symptemist_entities_source",
            version=SOURCE_VERSION,
            description="SympTEMIST (subtrack 1: entities) source schema",
            schema="source",
            subset_id="symptemist_entities",
        ),
        BigBioConfig(
            name="symptemist_linking_source",
            version=SOURCE_VERSION,
            description="SympTEMIST (subtrack 2: linking) source schema",
            schema="source",
            subset_id="symptemist_linking",
        ),
        BigBioConfig(
            name="symptemist_entities_bigbio_kb",
            version=BIGBIO_VERSION,
            description="SympTEMIST (subtrack 1: entities) BigBio schema",
            schema="bigbio_kb",
            subset_id="symptemist_entities",
        ),
        BigBioConfig(
            name="symptemist_linking_bigbio_kb",
            version=BIGBIO_VERSION,
            description="SympTEMIST (subtrack 2: linking) BigBio schema",
            schema="bigbio_kb",
            subset_id="symptemist_linking",
        ),
    ]

    DEFAULT_CONFIG_NAME = "symptemist_entities_source"

    def _info(self) -> datasets.DatasetInfo:

        if self.config.schema == "source":
            features = datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "document_id": datasets.Value("string"),
                    "passages": [
                        {
                            "id": datasets.Value("string"),
                            "type": datasets.Value("string"),
                            "text": datasets.Sequence(datasets.Value("string")),
                            "offsets": datasets.Sequence([datasets.Value("int32")]),
                        }
                    ],
                    "entities": [
                        {
                            "id": datasets.Value("string"),
                            "type": datasets.Value("string"),
                            "text": datasets.Sequence(datasets.Value("string")),
                            "offsets": datasets.Sequence([datasets.Value("int32")]),
                            "concept_codes": datasets.Sequence(datasets.Value("string")),
                            "semantic_relations": datasets.Sequence(datasets.Value("string")),
                        }
                    ],
                }
            )
        elif self.config.schema == "bigbio_kb":
            features = kb_features

        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=str(_LICENSE),
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager) -> List[datasets.SplitGenerator]:
        """Returns SplitGenerators."""
        urls = _URLS[_DATASETNAME]
        data_dir = dl_manager.download_and_extract(urls)
        base_bath = Path(data_dir) / "symptemist-train_all_subtasks+gazetteer+multilingual_230919"
        track = self.config.subset_id.split('_')[1]
                
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "split": "train",
                    "track": track,
                    "base_bath": base_bath,
                },
            ),
            #datasets.SplitGenerator(
            #    name=datasets.Split.TEST,
            #    gen_kwargs={
            #        "split": "test",
            #        "track": track,
            #        "base_bath": base_bath,
            #    },
            #),
        ]

    def _generate_examples(
        self,
        split: str, 
        track: str,
        base_bath: Path,
    ) -> Tuple[int, Dict]:
        """Yields examples as (key, example) tuples."""

        tsv_files = {
            ('entities', 'train'): [
                base_bath / "symptemist_train" / "subtask1-ner" / "tsv" / "symptemist_tsv_train_subtask1.tsv"
            ],
            #('entities', 'test'): [
            #    base_bath / "test_annotated" / "subtrack1_entities" / "symptemist_subtrack1_test_mentions.tsv"
            #],
            ('linking', 'train'): [
                base_bath / "symptemist_train" / "subtask2-linking" / "symptemist_tsv_train_subtask2.tsv"
            ],
            #('linking', 'test'): [
            #    base_bath / "test_annotated" / "subtrack2_linking" / "symptemist_subtrack2_test_linking.tsv"
            #],
        }

        entity_mapping_files = tsv_files[(track, split)]

        if split == "train":
            text_files_dir = base_bath / "symptemist_train" / "subtask1-ner" / "txt"
        #elif split == "test":
        #    text_files_dir = base_bath / "test_annotated" / "text_files"
        
        # keep this in case more files are added later
        entities_mapping = pd.concat([pd.read_csv(file, sep="\t") for file in entity_mapping_files])
        entity_file_names = entities_mapping["filename"].unique()
        
        for uid, filename in enumerate(entity_file_names):
            text_file = text_files_dir / f"{filename}.txt"

            doc_text = text_file.read_text(encoding='utf8')
            # doc_text = doc_text.replace("\n", "")

            entities_df: pd.DataFrame = entities_mapping[entities_mapping["filename"] == filename]

            example = {
                "id": f"{uid}",
                "document_id": filename,
                "passages": [
                    {
                        "id": f"{uid}_{filename}_passage",
                        "type": "clinical_case",
                        "text": [doc_text],
                        "offsets": [[0, len(doc_text)]],
                    }
                ],
            }
            if self.config.schema == "bigbio_kb":
                example["events"] = []
                example["coreferences"] = []
                example["relations"] = []

            entities = []
            for row in entities_df.itertuples(name="Entity"):
                
                entity = {
                    "id": f"{uid}_{row.filename}_{row.Index}_entity_id",#_{row.ann_id}",
                    "type": row.label,
                    "text": [row.text],
                    "offsets": [[row.start_span, row.end_span]] if self.config.subset_id == "symptemist_entities" else [[row.span_ini, row.span_end]],
                }
                
                if self.config.schema == "source":
                    entity["concept_codes"] = []
                    entity["semantic_relations"] = []
                    if self.config.subset_id == "symptemist_linking":
                        entity["concept_codes"] = row.code.split("+")
                        entity["semantic_relations"] = row.sem_rel.split("+")

                elif self.config.schema == "bigbio_kb":
                    if self.config.subset_id == "symptemist_linking":
                        entity["normalized"] = [
                            {"db_id": code, "db_name": "SNOMED_CT"} for code in row.code.split("+")
                        ]
                    else:
                        entity["normalized"] = []

                entities.append(entity)

            example["entities"] = entities
            yield uid, example