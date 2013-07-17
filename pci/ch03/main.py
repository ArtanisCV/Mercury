import clusters

__author__ = 'Artanis'


(blogNames, words, data) = clusters.readFile('blogData.txt')

blogClust = clusters.hcluster(data)
clusters.printClust(blogClust, blogNames, 0)
clusters.drawDendrogram(blogClust, blogNames, 'blogClusters.jpg')

wordClust = clusters.hcluster(clusters.rotateMatrix(data))
clusters.drawDendrogram(wordClust, words, 'wordClusters.jpg')

