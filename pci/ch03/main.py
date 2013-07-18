import time
import clusters

__author__ = 'Artanis'


(blogNames, words, data) = clusters.readFile('blogData.txt')

start = time.clock()
blogClust = clusters.hCluster(data)
print "Total Time:" + str(time.clock() - start)

# clusters.printClust(blogClust, blogNames, 0)
# clusters.drawDendrogram(blogClust, blogNames, 'blogClusters.jpg')
#
# wordClust = clusters.hCluster(clusters.rotateMatrix(data))
# clusters.drawDendrogram(wordClust, words, 'wordClusters.jpg')

start = time.clock()
kClust = clusters.kCluster(data, 10)
print "Total Time:" + str(time.clock() - start)

print len(kClust[0]), [blogNames[idx] for idx in kClust[0]]
print len(kClust[1]), [blogNames[idx] for idx in kClust[1]]