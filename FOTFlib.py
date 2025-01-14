#Description:
'''
    1. Overview:
        The following code is our final project algorithm for proofing a new concept of video compression.
        The final product will be in a client-server format, here we are just simulating with all of the code in one project, but the functions are independent. We can switch to client server format at any time.

        The product has 2 phases, the first will be preprocessing where the server learn the information is needs beforehand. And the second which will happen in a live stream of information.
        Here we will demonstrate the 2 phases in one run of the Main- the server is given images to learn the road, and later he uses what he learns at the second phase.
        Let us explain the process:
        The server is given a set of images (the images are from the same GPS location)
        The server calculates and learn the constants in the Images it’s given and saves them in memory, later to be used.
•	    In the final product the outcome of the calculation will be saved at a Database under a key of which is the GPS location.
        Then the algorithm is given another image, which is the “client’s” image, it is just a different image from the same GPS location. This will simulate a driver driving in this location.
        The server will send its outcome that was send in the DB to the client according to the key (GPS location).
        The client’s algorithm will compare the image and the data from the server.
        Then the client will send to the server the outcome of its calculations.
        The server then can paste back parts of the images and make more visible and understandable image.


    2. walktrough:
        one main function at the buttom that operate all of the following functions:
        Phase A, creating "common image"- the constants of all the images it's given
        3.1.1 getting an array of images and splitting it to diffrent arrays according to image similarity
        3.1.2 for each array, find the intersect of keypoints
        3.1.3 cluster the keypoints using dbscan and save.
        Phase B
        3.2.1  when given GPS, send the clusters and it's location in the image to the client
        Phase C - client side
        3.3.1 given client GPS, send to server ask for image(clsuters)
        3.3.2 check each cluster if found in camera's image
        3.3.3.1 if cluster found
        3.3.3.2 if cluster not found
        3.3.3.3 if area with no features on either side
        3.3.3 - to be decided
        Phase D - Server Side
        3.4.1 gets the non-matching parts.
        3.4.2 joining the clusters and new parts into an image.
    * the main function receives a :
    source folder which contains the images which the server should learn from,
    location of a client's image,
    wanted folder for the algorithm outputs.
'''
from functions import *
outputFolder=''
from objects import *
import cv2
import matplotlib.pyplot as plt
#creating paths and basic information for the YOLO object detection algorithm.
yoloLabels = 'ObjectDalgorithm/yoloLabels.txt'
yoloWeights = 'ObjectDalgorithm/yolov3.weights'
yoloConfig = 'ObjectDalgorithm/yolov3.cfg'
threshold_ob = 0.5

def main(serverFolder,clientImg,outputFolder,threshold,dbscan_epsilon):#threshold - precentege of matches in order to consider good cluster
    getFolder(outputFolder)

    #SERVER:
    #preprocessing, load, sort and divide images
    serverImgArrayWithSameGps = find_imgs_same_gps(clientImg,serverFolder)
    print(serverImgArrayWithSameGps)

    SortedArrayimg=buildaArrayImages(serverImgArrayWithSameGps)
    temp=SortedArrayimg[0]
    #SortedArrayimg=buildaArrayImages(serverFolder)

    ###
    #Object detection section: returns ranges(yStart,yEnd,xStart,xEnd) of each object
    range_list = findObjectsUsingYOLO(SortedArrayimg[0],yoloLabels,yoloWeights,yoloConfig,threshold_ob)

    flagarrayOfObjects=[0]*(len(range_list))
    print("FLAGS ARE ",flagarrayOfObjects)
    print(len(range_list),"the len of all objects")
    #get the key,des of the first picture with the most features
    kp, des = firstFuncCheck(SortedArrayimg[0])
    #list of tupels(key,des) of each object
    listOfObjects = keyOfObject(range_list,kp,des)#Comparing the objects and keypoints
    print(len(listOfObjects),"should be 7")
    #list of matched objects from all the pictures
    listOfMatches = IntersectOfImages2(listOfObjects, SortedArrayimg)#check if the objects is in the other imags
    #print(len(range_list), "len range list, number of objects")
    #print(len(listOfObjects), "list of object")
    #print(len(listOfMatches),"list of matches")

    croped = SortedArrayimg[0]
    #remove the best matched objects with high ration from the first picture
    croped, new_listOfMatches, listOfNumbers,flagarrayOfObjects = matchedObjects(listOfMatches, range_list, croped,flagarrayOfObjects)
    #build the remove array of objects
    print(len(new_listOfMatches),"list of objects match in all pictures")
    print(len(listOfNumbers), "list of objects match in all pictures")
    newArray, newIndexarray=initIndexObjectarray(flagarrayOfObjects)#array to paste objects


    #overwrite the first picture with the croped
    SortedArrayimg[0] = croped
    cv2.imwrite(outputFolder+'/after_objects_off.jpg', croped)
    kp_1, des_1 = IntersectOfImages(SortedArrayimg)# find inersect of features on all images:
    dictionary = CreateDict(kp_1, des_1) #dictionary between coordinates and keypoints+descriptors:
    #adding to the current dictionary the clusters of objects
    dictionary=updateDict(dictionary,new_listOfMatches)
    print(len(dictionary))
    #build clusters and then we adding the objects clusters
    clusters,NClustersWObjects=updateCluster(kp_1,dbscan_epsilon,new_listOfMatches)
    print(NClustersWObjects," number of cluster without objects")
    print(len(clusters),"all the clusters")

    dict=makeDictforOriginalClusters(clusters)
    print("Number of original clusters: ",len(clusters))



    #CLIENT
    ClientImage=cv2.imread(clientImg) # read client image

    #good clusters-matched clusters between the server and client

    arrayOfGoodclusters,flagsOfGoodClusters,arrayOfBadclusters,flagsOfBadClusters,newListOfNumbers,count_originals,newIndexarray = makegoodclusters(clusters,dictionary,ClientImage,threshold,NClustersWObjects,listOfNumbers,newIndexarray) #find good clusters and bad clusters


    print("new index array after change ",newIndexarray)
    print(count_originals,"the number of regular clusers that are good")
    print(len(newListOfNumbers),"the number of good objects")

    dict2=makeDictforGoodClusters(arrayOfGoodclusters[:count_originals],flagsOfGoodClusters)
    #dict3=makeDictforBadClusters(arrayOfBadclusters,flagsOfBadClusters)
    print(len(arrayOfGoodclusters),"array of good clusters")
    #drop the good clusters from the client image
    croppedimage = makecroppedimage(arrayOfGoodclusters,ClientImage,newListOfNumbers,count_originals,range_list) # drop the areas of clusters found in the client image that match the server image
    cv2.imwrite(outputFolder+'/cropped2.jpg', croppedimage)
    print("CROPPED ! GO CHECK IT OUT !")

    print("SECOND PLOT")
    #Object detection section: returns ranges(yStart,yEnd,xStart,xEnd) of each object-on the croppedimage
    secondRange_list = findObjectsUsingYOLO(croppedimage, yoloLabels, yoloWeights, yoloConfig, threshold_ob)
    print(len(secondRange_list),"objectssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss")

    new_cropped=croppedimage
    #remove the clients objects from the cropped image
    #for i in range(0,len(secondRange_list)):
    #    new_cropped = imageDeleteObject(new_cropped, secondRange_list[i])
    for j in secondRange_list:
        new_cropped = imageDeleteObject(new_cropped, j)


    print("third PLOT")
    #take out the new clusters from the client image in order to send
    Newclusters2, Newdictionary2, kp3, des3 = clustersOfCroppedImage(new_cropped,dbscan_epsilon)
    #newimage is the cropped image after cropping sift clusters from it
    newimage=makecroppedimage2(Newclusters2,new_cropped)
    cv2.imwrite(outputFolder+'/clusters_of_cropped2.jpg', newimage)
    cv2.imwrite(outputFolder+'/clusters_to_send2.jpg', croppedimage-newimage) # the negetivity in order to send to. makes it that we send just the clusters we found after first cropped
    #return the changed parts
    imagetosend =croppedimage-newimage
    imagetotakeclustersfrom = SortedArrayimg[len(SortedArrayimg)-1]
    imagetosend=returnCroppedParts(imagetosend,imagetotakeclustersfrom,dict2,dict) #for better understanding of image, on server side, return parts of good clusters and bad clsuters:
    returnobjects(imagetosend,temp,newIndexarray,range_list,outputFolder,newArray)

    #imgafterBadclustersreturn = returnCroppedParts2(imgafterGoodclustersreturn,imagetotakeclustersfrom,dict3, dict)
    #
    '''
    src = cv2.imread('clusters_to_send.jpg', 1)
    
    tmp = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    _,alpha = cv2.threshold(tmp,0,255,cv2.THRESH_BINARY)
    b, g, r = cv2.split(src)
    rgba = [b,g,r, alpha]
    dst = cv2.merge(rgba,4)
    cv2.imwrite("test.jpeg", dst)
    
    counter=0
    for cluster in Newclusters:
        minY, maxY, minX, maxX = corMinMax(cluster)
        crop_img = croppedimage[int(minY):int(maxY),
                   int(minX):int(maxX)]
        cv2.imwrite('newcropped' + str(counter) + '.jpg', crop_img)
        counter=counter+1
    
    #in new cameras image(after parts removed) do funccheck
    #cluster the featuers that returned.
    #crop the parts of clusters found in cameras image and return them.
    #to do - check for location of cropped parts in order to tell the server where they are located in server image.
    '''



threshhold=0.25
dbscan=10
'''
main receives the following information which some you can change:
 1. source folder dir, 2. client image location, 3. output folder dir ,threshold- do not change, dbscan- do not change : 
'''
#main("source/test_4.8.19/1/server1", "source/test_4.8.19/1/client1/1.jpg", "source/test_4.8.19/1/output", threshhold,dbscan)
#main("source/test_4.8.19/2/server2", "source/test_4.8.19/2/client2/2.jpg", "source/test_4.8.19/2/output", threshhold,dbscan)
#main("source/test_4.8.19/3/server2", "source/test_4.8.19/3/client3/3.jpg", "source/test_4.8.19/3/output", threshhold,dbscan)
#main("source/test_4.8.19/4/server", "source/test_4.8.19/4/client/220.jpg", "source/test_4.8.19/4/output", threshhold,dbscan)



main("source/pics_for_tests/1/server", "source/pics_for_tests/1/client/6.jpg", "source/pics_for_tests/1/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/1/server", "source/pics_for_tests/1/client/10.jpg", "source/pics_for_tests/1/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/1/server", "source/pics_for_tests/1/client/13.jpg", "source/pics_for_tests/1/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/3/server", "source/pics_for_tests/3/client/19.jpg", "source/pics_for_tests/3/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/3/server", "source/pics_for_tests/3/client/90.jpg", "source/pics_for_tests/3/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/3/server", "source/pics_for_tests/3/client/277.jpg", "source/pics_for_tests/3/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/4/server", "source/pics_for_tests/4/client/115.jpg", "source/pics_for_tests/4/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/4/server", "source/pics_for_tests/4/client/121.jpg", "source/pics_for_tests/4/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/4/server", "source/pics_for_tests/4/client/183.jpg", "source/pics_for_tests/4/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/5/server", "source/pics_for_tests/5/client/115.jpg", "source/pics_for_tests/5/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/6/server", "source/pics_for_tests/6/client/97.jpg", "source/pics_for_tests/6/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/7/server", "source/pics_for_tests/7/client/186.jpg", "source/pics_for_tests/7/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/8/server", "source/pics_for_tests/8/client/120.jpg", "source/pics_for_tests/8/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/9/server", "source/pics_for_tests/9/client/73.jpg", "source/pics_for_tests/9/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/9/server", "source/pics_for_tests/9/client/77.jpg", "source/pics_for_tests/9/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/10/server", "source/pics_for_tests/10/client/115.jpg", "source/pics_for_tests/10/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/11/server", "source/pics_for_tests/11/client/204.jpg", "source/pics_for_tests/11/output/" + str(threshhold), threshhold,10)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/87.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/88.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/113.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/115.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/117.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/122.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/127.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/13/server", "source/pics_for_tests/13/client/20190602_172935(0).jpg", "source/pics_for_tests/13/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/14/server", "source/pics_for_tests/14/client/4.jpg", "source/pics_for_tests/14/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/14/server", "source/pics_for_tests/14/client/20190602_172914.jpg", "source/pics_for_tests/14/output/" + str(threshhold), threshhold,dbscan)
#main("source/pics_for_tests/15/server", "source/pics_for_tests/15/client/11.jpg", "source/pics_for_tests/15/output/" + str(threshhold), threshhold,dbscan)

#gps example
#main("GPS/pics_for_gps", "GPS/pics_for_gps/20190603_172000.jpg", "output/" + str(threshhold), threshhold,dbscan)





'''
main("source/pics_for_tests/1/server", "source/pics_for_tests/1/client/6.jpg", "source/pics_for_tests/1/output/" + str(threshhold), threshhold,dbscan)
main("source/pics_for_tests/5/server", "source/pics_for_tests/5/client/115.jpg", "source/pics_for_tests/5/output/" + str(threshhold), threshhold,dbscan)
main("source/pics_for_tests/6/server", "source/pics_for_tests/6/client/97.jpg", "source/pics_for_tests/6/output/" + str(threshhold), threshhold,dbscan)
main("source/pics_for_tests/7/server", "source/pics_for_tests/7/client/186.jpg", "source/pics_for_tests/7/output/" + str(threshhold), threshhold,dbscan)
main("source/pics_for_tests/8/server", "source/pics_for_tests/8/client/120.jpg", "source/pics_for_tests/8/output/" + str(threshhold), threshhold,dbscan)
main("source/pics_for_tests/11/server", "source/pics_for_tests/11/client/204.jpg", "source/pics_for_tests/11/output/" + str(threshhold), threshhold,10)
main("source/pics_for_tests/12/server", "source/pics_for_tests/12/client/127.jpg", "source/pics_for_tests/12/output/" + str(threshhold), threshhold,dbscan)
'''

#Reliability check
'''
client=cv2.imread("source/pics_for_tests/12/client/127.jpg")
paste=cv2.imread("source/pics_for_tests/12/output/0.25/croppedOmriClient000.jpg")
p,okp,odes,lenKp2,lenKp1=funcCheck1(client,paste)

print("p/okp client-paste")
print(p,lenKp2,lenKp1)
#print(p/lenKp2)
print((lenKp1+lenKp2)/(2*p))

p,okp,odes,lenKp2,lenKp1=funcCheck1(paste, client)
print("p/okp paste-client")
print(p,lenKp2,lenKp1)

#print(p/lenKp2)
print((lenKp1+lenKp2)/(2*p))



print("objects client")
print(len(findObjectsUsingYOLO(client,yoloLabels,yoloWeights,yoloConfig,threshold_ob)))
print("objects paste")
print(len(findObjectsUsingYOLO(paste,yoloLabels,yoloWeights,yoloConfig,threshold_ob)))

'''