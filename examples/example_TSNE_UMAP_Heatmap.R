###########################################################################################
# Example script for running with singularity
# 
# Wout Megchelenbrink
#
# Last update: May 06, 2020
###########################################################################################
rm(list=ls())
library(Seurat)
library(ggplot2)
library(ComplexHeatmap)
library(circlize)

# Load RDS file
Zic3KO <- readRDS("scRNAseq_Zic3_WT_and_KO.Rds")

# Subset
Zic3KO <- subset(x = Zic3KO, subset = nCount_RNAseq >= 10000 &
                                      nFeature_RNAseq >= 2000 & 
                                      percent.mito < 25)

Zic3KO <- NormalizeData(object = Zic3KO, normalization.method = "LogNormalize", scale.factor = 10000)
Zic3KO <- ScaleData(object = Zic3KO)

Zic3KO <- FindVariableFeatures(Zic3KO)
Zic3KO <- RunPCA(object = Zic3KO)

Zic3KO <- RunUMAP(Zic3KO, dims =1:12)
UMAPPlot(Zic3KO, group.by = "plate", shape = "medium")
ggsave(filename = "UMAP_Zic3KO_12dims.pdf", width = 7, height = 4)

cols.cluster <- RColorBrewer::brewer.pal(n=5, name="Set1")
names(cols.cluster) <- 0:4


Zic3KO <- FindNeighbors(Zic3KO, dims = 1:12)
Zic3KO <- FindClusters(Zic3KO, resolution = 0.1)
UMAPPlot(object = Zic3KO,  shape = "medium") +
scale_color_manual(values = cols.cluster)
ggsave(filename = "UMAP_Zic3KO_12dims_clustered_0.1_resolution_mod_0.95.pdf", width = 7, height = 4)



### Heatmap for selected cluster markers #####
genes <- c("Nanog", "Tcfcp2l1", "Tbx3", "Prdm14", "Tet2", # 2iL WT
         "Zic3",  "Lefty1",  "Skil",  "Sox2", "Emb", "Trh", "Gbx2", "Zfp462", # SL WT
         "Trim28", "Dnmt3a", "Dnmt3b", "Dnmt3l", "Bmp4", "Utf1",  # SL KO
          "Sox7", "Sox17", "Gata4", "Gata6") # PrE

split <- c(rep(1, 5),  rep(2,8), rep(3, 6), rep(4,4))

# Grep these guys from the expression matrix; annotate genotype, cluster, medium; do hierarch clustering
mat <- Seurat::GetAssayData(Zic3KO, assay = "RNAseq", slot = "scale.data")
mat <- mat[genes, ]

cols.genotype <- c("blue3", "#666666")
names(cols.genotype) <- c("WT", "Zic3KO")

cols.medium <- c("#222222", "#BBBBBB")
names(cols.medium) <- c("ser", "2i")


Zic3KO$seurat_clusters <- factor(Zic3KO$seurat_clusters, levels = c(0,2,1,3))

# Order clusters
ID <- c(which(Zic3KO$seurat_clusters == 0),
        which(Zic3KO$seurat_clusters == 2),
        which(Zic3KO$seurat_clusters == 1),
        which(Zic3KO$seurat_clusters == 3))

# Annotate clusters
ha <- HeatmapAnnotation(cluster = factor(Zic3KO$seurat_clusters[ID]),
                        medium = Zic3KO$medium[ID],
                        genotype = Zic3KO$genotype[ID],
                        col = list(cluster = cols.cluster,
                                   genotype = cols.genotype,
                                   medium = cols.medium),
                                   gp = gpar(border=F, col=NA, cex=0, lwd=0))

# Make heatmap and save as PDF
pdf("Heatmap_clusters_0_4.pdf", width = 6, height = 5)
Heatmap(mat[, ID], name = "Heatmap", cluster_rows = F, cluster_columns = F, col = colorRamp2(seq(-2,2,length.out = 10), PurpleAndYellow(10)),
        show_column_names = F, show_row_dend = F, show_column_dend = F, top_annotation = ha, split=split,  rect_gp = gpar(border=F, col=NA, cex=0, lwd=0), 
        use_raster = T, raster_quality = 2, raster_device = "CairoPNG")
dev.off()
