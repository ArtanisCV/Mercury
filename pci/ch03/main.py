import clusters

__author__ = 'Artanis'


(blogNames, words, data) = clusters.readFile('blogData.txt')
clust = clusters.hcluster(data)
clusters.printClust(clust, blogNames, 0)
clusters.drawDendrogram(clust, blogNames, 'blogClusters.jpg')